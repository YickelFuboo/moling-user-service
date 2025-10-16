import logging
import json
import secrets
import hashlib
import base64
import time
from datetime import datetime
from typing import Optional, Dict, Any
import httpx
import jwt
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from app.config.settings import settings
from app.infrastructure.redis.factory import REDIS_CONN
from app.models.user import User
from app.services.auth_mgmt.jwt_service import JWTService
from app.services.auth_mgmt.auth_service import AuthService
from app.services.auth_mgmt.password_service import PasswordService
from app.services.auth_mgmt.verify_code_service import VerifyCodeService
from app.services.user_mgmt.user_service import UserService


class OAuthService:
    """OAuth服务类"""
    
    # OAuth提供商配置 - 直接在类级别定义，无需初始化方法
    OAUTH_PROVIDERS = {
        "github": {
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "redirect_uri": settings.github_redirect_uri,
            "auth_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "user_info_url": "https://api.github.com/user"
        },
        
        "google": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo"
        },
        
        "wechat": {
            "client_id": settings.wechat_app_id,
            "client_secret": settings.wechat_app_secret,
            "redirect_uri": settings.wechat_redirect_uri,
            "auth_url": "https://open.weixin.qq.com/connect/qrconnect",
            "token_url": "https://api.weixin.qq.com/sns/oauth2/access_token",
            "user_info_url": "https://api.weixin.qq.com/sns/userinfo"
        },
        
        "alipay": {
            "client_id": settings.alipay_app_id,
            "client_secret": settings.alipay_private_key,
            "redirect_uri": settings.alipay_redirect_uri,
            "auth_url": "https://openauth.alipay.com/oauth2/publicAppAuthorize.htm",
            "token_url": "https://openapi.alipay.com/gateway.do",
            "user_info_url": "https://openapi.alipay.com/gateway.do"
        }
    }
    
    @staticmethod
    def _generate_redis_key(value: str) -> str:
        """生成Redis键"""
        return f"oauth_state:{value}"
    
    @classmethod
    def get_oauth_provider(cls, provider: str) -> Optional[Dict[str, str]]:
        """获取OAuth提供商配置"""
        provider_config = cls.OAUTH_PROVIDERS.get(provider)
        if not provider_config:
            return None
        
        # 检查是否配置了必要的参数
        if provider == "github":
            if not (provider_config.get("client_id") and provider_config.get("client_secret")):
                return None
        elif provider == "google":
            if not (provider_config.get("client_id") and provider_config.get("client_secret")):
                return None
        elif provider == "wechat":
            if not (provider_config.get("client_id") and provider_config.get("client_secret")):
                return None
        elif provider == "alipay":
            if not (provider_config.get("client_id") and provider_config.get("client_secret")):
                return None
        
        return provider_config
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, Dict[str, str]]:
        """获取所有可用的OAuth提供商"""
        available_providers = {}
        
        for provider, config in cls.OAUTH_PROVIDERS.items():
            # 检查是否配置了必要的参数
            if provider == "github":
                if config.get("client_id") and config.get("client_secret"):
                    available_providers[provider] = config
            elif provider == "google":
                if config.get("client_id") and config.get("client_secret"):
                    available_providers[provider] = config
            elif provider == "wechat":
                if config.get("client_id") and config.get("client_secret"):
                    available_providers[provider] = config
            elif provider == "alipay":
                if config.get("client_id") and config.get("client_secret"):
                    available_providers[provider] = config
        
        return available_providers
    
    @staticmethod
    def _validate_state_parameter(state: str, expected_state: str) -> bool:
        """验证state参数"""
        return state == expected_state
    
    @staticmethod
    async def generate_state_parameter() -> str:
        """生成state参数"""
        state = secrets.token_urlsafe(32)
        # 存储state参数到Redis，设置5分钟过期
        state_data = {
            "created_at": datetime.utcnow().isoformat(),
            "used": False
        }
        redis_key = OAuthService._generate_redis_key(state)
        await REDIS_CONN.set(redis_key, state_data, expire=300)
        return state
    
    @staticmethod
    async def _get_and_consume_state(state: str) -> bool:
        """获取并消费state参数"""
        redis_key = OAuthService._generate_redis_key(state)
        state_data = await REDIS_CONN.get(redis_key)
        
        if state_data is None:
            return False
        
        # 检查是否已使用
        if state_data.get("used", False):
            return False
        
        # 直接删除，无需标记
        await REDIS_CONN.delete(redis_key)
        return True
    
    @staticmethod
    async def handle_oauth_login(session: AsyncSession, provider: str, code: str, state: Optional[str] = None, client_ip: Optional[str] = None) -> Dict[str, Any]:
        """处理OAuth登录"""
        try:
            # 验证state参数（如果提供了）
            if state:
                if not await OAuthService._get_and_consume_state(state):
                    raise ValueError("State参数验证失败或已过期")
            
            # 获取OAuth提供商配置
            oauth_provider = OAuthService.get_oauth_provider(provider)
            if not oauth_provider:
                raise ValueError(f"未找到{provider}提供商配置")
            
            # 获取访问令牌
            access_token = await OAuthService._get_access_token(provider, code, oauth_provider)
            if not access_token:
                raise ValueError(f"获取{provider}访问令牌失败")
            
            # 获取用户信息
            user_info = await OAuthService.get_user_info(provider, access_token)
            if not user_info:
                raise ValueError(f"获取{provider}用户信息失败")
            
            # 创建或更新用户
            user = await OAuthService._create_or_update_user_from_oauth(session, provider, user_info)
            
            # 使用统一的登录响应创建函数
            return await AuthService.create_login_response(session, user, client_ip)
            
        except Exception as e:
            logging.error(f"处理{provider}登录失败: {e}")
            raise
    
    @staticmethod
    async def _get_access_token(provider: str, code: str, oauth_provider: Dict[str, str]) -> Optional[str]:
        """获取访问令牌"""
        max_retries = 3
        retry_delay = 1  # 秒
        
        for attempt in range(max_retries):
            try:
                data = {
                    "client_id": oauth_provider["client_id"],
                    "client_secret": oauth_provider["client_secret"],
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": oauth_provider["redirect_uri"]
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(oauth_provider["token_url"], data=data, timeout=10)
                    
                    if response.status_code == 200:
                        token_data = response.json()
                        return token_data.get("access_token")
                    else:
                        logging.error(f"获取{provider}访问令牌失败: {response.status_code} - {response.text}")
                        if attempt < max_retries - 1:
                            import asyncio
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2  # 指数退避
                            continue
                        return None
                        
            except Exception as e:
                logging.error(f"获取{provider}访问令牌异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                return None
        
        return None
    
    @staticmethod
    async def get_user_info(provider: str, access_token: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        if provider == "github":
            return await OAuthService._get_github_user_info(access_token)
        elif provider == "google":
            return await OAuthService._get_google_user_info(access_token)
        elif provider == "wechat":
            # 微信需要openid，这里简化处理
            return await OAuthService._get_wechat_user_info(access_token, "openid")
        elif provider == "alipay":
            return await OAuthService._get_alipay_user_info(access_token)
        else:
            raise ValueError(f"不支持的OAuth提供商: {provider}")
    
    @staticmethod
    async def _get_github_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """获取GitHub用户信息"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.github.com/user",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logging.error(f"获取GitHub用户信息失败: {response.status_code}")
                    return None
                    
        except Exception as e:
            logging.error(f"获取GitHub用户信息异常: {e}")
            return None
    
    @staticmethod
    async def _get_google_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """获取Google用户信息"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logging.error(f"获取Google用户信息失败: {response.status_code}")
                    return None
                    
        except Exception as e:
            logging.error(f"获取Google用户信息异常: {e}")
            return None
    
    @staticmethod
    async def _get_wechat_user_info(access_token: str, openid: str) -> Optional[Dict[str, Any]]:
        """获取微信用户信息"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.weixin.qq.com/sns/userinfo",
                    params={
                        "access_token": access_token,
                        "openid": openid,
                        "lang": "zh_CN"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("errcode") == 0:
                        return data
                    else:
                        logging.error(f"获取微信用户信息失败: {data}")
                        return None
                else:
                    logging.error(f"获取微信用户信息失败: {response.status_code}")
                    return None
                    
        except Exception as e:
            logging.error(f"获取微信用户信息异常: {e}")
            return None
    
    @staticmethod
    async def _get_alipay_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """获取支付宝用户信息"""
        try:
            # 支付宝用户信息获取需要特殊的签名处理
            # 这里简化处理，实际需要按照支付宝API规范
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://openapi.alipay.com/gateway.do",
                    params={
                        "method": "alipay.user.info.share",
                        "app_id": "your_app_id",
                        "format": "json",
                        "charset": "utf-8",
                        "sign_type": "RSA2",
                        "timestamp": "2023-01-01 00:00:00",
                        "version": "1.0",
                        "auth_token": access_token
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logging.error(f"获取支付宝用户信息失败: {response.status_code}")
                    return None
                    
        except Exception as e:
            logging.error(f"获取支付宝用户信息异常: {e}")
            return None

    @staticmethod
    async def _get_oidc_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """获取OIDC用户信息"""
        try:
            # OIDC通常返回JWT格式的ID令牌
            
            # 解码JWT令牌（不验证签名，仅获取信息）
            try:
                decoded = jwt.decode(access_token, options={"verify_signature": False})
                return {
                    "id": decoded.get("sub"),
                    "email": decoded.get("email"),
                    "username": decoded.get("preferred_username") or decoded.get("name"),
                    "full_name": decoded.get("name"),
                    "avatar": decoded.get("picture")
                }
            except jwt.InvalidTokenError:
                # 如果不是JWT，尝试作为普通OAuth令牌使用
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://your-oidc-provider.com/userinfo",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    if response.status_code == 200:
                        return response.json()
                    else:
                        logging.error(f"获取OIDC用户信息失败: {response.status_code}")
                        return None
                        
        except Exception as e:
            logging.error(f"获取OIDC用户信息异常: {e}")
            return None

    @staticmethod
    async def _create_or_update_user_from_oauth(session: AsyncSession, provider: str, oauth_user_info: Dict[str, Any]) -> User:
        """从OAuth用户信息创建或更新用户"""
        try:
            # 根据提供商获取用户ID
            provider_id_field = f"{provider}_id"
            oauth_id = oauth_user_info.get("id") or oauth_user_info.get("openid")
            
            if not oauth_id:
                raise ValueError(f"无法获取{provider}用户ID")
            
            # 查找现有用户
            result = await session.execute(
                select(User).where(getattr(User, provider_id_field) == oauth_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                # 更新现有用户信息
                user.user_full_name = oauth_user_info.get("name") or oauth_user_info.get("login")
                user.avatar = oauth_user_info.get("avatar_url")
                await session.commit()
                logging.info(f"更新{provider}用户: {user.user_name}")
            else:
                # 创建新用户
                username = oauth_user_info.get("login") or oauth_user_info.get("name") or f"{provider}_{oauth_id}"
                email = oauth_user_info.get("email")
                
                # 确保用户名唯一
                username = await UserService.generate_unique_username(session, username)
                
                # 生成随机密码
                random_password = PasswordService.generate_random_password(16)
                
                # 使用UserService创建用户
                user_data = {
                    "user_name": username,
                    "email": email,
                    "user_full_name": oauth_user_info.get("name") or oauth_user_info.get("login"),
                    "avatar": oauth_user_info.get("avatar_url"),
                    "hashed_password": PasswordService.hash_password(random_password),
                    **{provider_id_field: oauth_id}
                }
                
                user = await UserService.create_user_with_default_role(session, user_data, provider)
                logging.info(f"创建{provider}用户: {user.user_name}")
            
            return user
            
        except Exception as e:
            logging.error(f"创建或更新{provider}用户失败: {e}")
            raise

    @staticmethod
    async def bind_oauth_account(session: AsyncSession, user_id: str, provider: str, oauth_user_info: Dict[str, Any]) -> bool:
        """绑定OAuth账号"""
        try:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return False
            
            provider_id_field = f"{provider}_id"
            oauth_id = oauth_user_info.get("id") or oauth_user_info.get("openid")
            
            if not oauth_id:
                return False
            
            # 检查是否已被其他用户绑定
            result = await session.execute(
                select(User).where(getattr(User, provider_id_field) == oauth_id)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user and existing_user.id != user_id:
                return False
            
            # 绑定账号
            setattr(user, provider_id_field, oauth_id)
            await session.commit()
            
            logging.info(f"用户{user.user_name}绑定{provider}账号成功")
            return True
            
        except Exception as e:
            logging.error(f"绑定{provider}账号失败: {e}")
            return False
    
    @staticmethod
    async def unbind_oauth_account(session: AsyncSession, user_id: str, provider: str) -> bool:
        """解绑OAuth账号"""
        try:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return False
            
            provider_id_field = f"{provider}_id"
            setattr(user, provider_id_field, None)
            await session.commit()
            
            logging.info(f"用户{user.user_name}解绑{provider}账号成功")
            return True
            
        except Exception as e:
            logging.error(f"解绑{provider}账号失败: {e}")
            return False 

    @staticmethod
    async def handle_oidc_login(session: AsyncSession, issuer: str, code: str, state: Optional[str] = None, client_ip: Optional[str] = None) -> Dict[str, Any]:
        """处理OIDC登录"""
        try:
            # 发现OIDC配置
            oidc_config = await OAuthService.discover_oidc_config(issuer)
            if not oidc_config:
                raise ValueError(f"无法发现OIDC配置: {issuer}")
            
            # 获取访问令牌和ID令牌
            token_response = await OAuthService._get_oidc_tokens(issuer, code, oidc_config)
            if not token_response:
                raise ValueError("获取OIDC令牌失败")
            
            access_token = token_response.get("access_token")
            id_token = token_response.get("id_token")
            
            # 从ID令牌获取用户信息
            user_info = await OAuthService._get_oidc_user_info(id_token)
            if not user_info:
                raise ValueError("获取OIDC用户信息失败")
            
            # 创建或更新用户
            user = await OAuthService._create_or_update_user_from_oauth(session, "oidc", user_info)
            
            # 使用统一的登录响应创建函数
            return await AuthService.create_login_response(session, user, client_ip)
            
        except Exception as e:
            logging.error(f"处理OIDC登录失败: {e}")
            raise
    
    @staticmethod
    async def _get_oidc_tokens(issuer: str, code: str, oidc_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """获取OIDC令牌"""
        try:            
            data = {
                "client_id": settings.oidc_client_id,
                "client_secret": settings.oidc_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.oidc_redirect_uri
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(oidc_config["token_endpoint"], data=data)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logging.error(f"获取OIDC令牌失败: {response.status_code}")
                    return None
                    
        except Exception as e:
            logging.error(f"获取OIDC令牌异常: {e}")
            return None
    
    @staticmethod
    async def discover_oidc_config(issuer: str) -> Optional[Dict[str, Any]]:
        """OIDC配置发现"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{issuer}/.well-known/openid-configuration")
                if response.status_code == 200:
                    return response.json()
                else:
                    logging.error(f"OIDC配置发现失败: {response.status_code}")
                    return None
        except Exception as e:
            logging.error(f"OIDC配置发现异常: {e}")
            return None
