import logging
from typing import Optional
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemes.auth import OAuthLogin, OAuthBind, OIDCLogin
from app.infrastructure.database.factory import get_db
from app.services.auth_mgmt.oauth_service import OAuthService
from app.api.deps import get_request_language
from app.services.common.i18n_service import I18nService


router = APIRouter()


@router.get("/providers")
async def get_oauth_providers(
    language: str = Depends(get_request_language)
):
    """
    获取可用的OAuth提供商列表
    
    Returns:
        提供商列表
    """
    try:
        providers = OAuthService.get_available_providers()
        
        return {
            "providers": [
                {
                    "provider": provider,
                    "name": provider.title(),
                    "auth_url": config["auth_url"]
                }
                for provider, config in providers.items()
            ]
        }
        
    except Exception as e:
        logging.error(f"获取OAuth提供商列表失败: {e}")
        raise HTTPException(status_code=500, detail=I18nService.get_error_message("server_error", language)) 

@router.get("/{provider}/authorize")
async def oauth_authorize(
    provider: str,
    language: str = Depends(get_request_language)
):
    """
    获取OAuth授权URL
    
    Args:
        provider: 提供商 (github, google, wechat, alipay, oidc)
    
    Returns:
        重定向到OAuth授权页面
    """
    try:
        oauth_provider = OAuthService.get_oauth_provider(provider)
        
        if not oauth_provider:
            raise HTTPException(status_code=404, detail=I18nService.get_error_message("oauth_provider_not_found", language))
        
        # 生成state参数
        state = await OAuthService.generate_state_parameter()
        
        # 构建授权URL
        auth_url = oauth_provider["auth_url"]
        params = {
            "client_id": oauth_provider["client_id"],
            "redirect_uri": oauth_provider["redirect_uri"],
            "response_type": "code",
            "state": state
        }
        
        # 添加scope参数
        if provider == "github":
            params["scope"] = "read:user user:email"
        elif provider == "google":
            params["scope"] = "openid email profile"
        elif provider == "wechat":
            params["scope"] = "snsapi_login"
        elif provider == "alipay":
            params["scope"] = "auth_user"
        elif provider == "oidc":
            params["scope"] = "openid email profile"
        
        # 构建完整URL
        full_url = f"{auth_url}?{urlencode(params)}"
        
        return RedirectResponse(url=full_url)
        
    except Exception as e:
        logging.error(f"获取{provider}授权URL失败: {e}")
        raise HTTPException(status_code=500, detail=I18nService.get_error_message("server_error", language))

@router.post("/{provider}/callback")
async def oauth_callback(
    provider: str,
    oauth_data: OAuthLogin,
    request: Request,
    language: str = Depends(get_request_language),
    session: AsyncSession = Depends(get_db)
):
    """
    OAuth回调处理
    
    Args:
        provider: 提供商
        oauth_data: OAuth数据
        session: 异步数据库会话
    
    Returns:
        登录结果
    """
    try:
        # 获取客户端IP
        client_ip = request.client.host
        
        result = await OAuthService.handle_oauth_login(
            session=session,
            provider=provider,
            code=oauth_data.code,
            state=oauth_data.state,
            client_ip=client_ip
        )
        
        return result
        
    except Exception as e:
        logging.error(f"{provider}登录失败: {e}")
        raise HTTPException(status_code=400, detail=I18nService.get_error_message("oauth_login_failed", language))

@router.post("/{provider}/bind")
async def bind_oauth_account(
    provider: str,
    oauth_bind: OAuthBind,
    language: str = Depends(get_request_language),
    session: AsyncSession = Depends(get_db)
):
    """
    绑定OAuth账号
    
    Args:
        provider: 提供商
        oauth_bind: 绑定数据
        session: 异步数据库会话
    
    Returns:
        绑定结果
    """
    try:
        # 获取OAuth用户信息
        user_info = await OAuthService.get_user_info(provider, oauth_bind.access_token)
        if not user_info:
            raise HTTPException(status_code=400, detail=I18nService.get_error_message("oauth_user_info_get_failed", language))
        
        # 绑定账号
        success = await OAuthService.bind_oauth_account(
            session=session,
            user_id=oauth_bind.user_id,
            provider=provider,
            oauth_user_info=user_info
        )
        
        if success:
            return {"message": I18nService.get_success_message("oauth_bind_success", language)}
        else:
            raise HTTPException(status_code=400, detail=I18nService.get_error_message("oauth_bind_failed", language))
            
    except Exception as e:
        logging.error(f"绑定{provider}账号失败: {e}")
        raise HTTPException(status_code=500, detail=I18nService.get_error_message("server_error", language))

@router.delete("/{provider}/unbind")
async def unbind_oauth_account(
    provider: str,
    user_id: str,
    language: str = Depends(get_request_language),
    session: AsyncSession = Depends(get_db)
):
    """
    解绑OAuth账号
    
    Args:
        provider: 提供商
        user_id: 用户ID
        session: 异步数据库会话
    
    Returns:
        解绑结果
    """
    try:
        success = await OAuthService.unbind_oauth_account(session, user_id, provider)
        
        if success:
            return {"message": I18nService.get_success_message("oauth_unbind_success", language)}
        else:
            raise HTTPException(status_code=400, detail=I18nService.get_error_message("oauth_unbind_failed", language))
            
    except Exception as e:
        logging.error(f"解绑{provider}账号失败: {e}")
        raise HTTPException(status_code=500, detail=I18nService.get_error_message("server_error", language))

@router.post("/oidc/callback")
async def oidc_callback(
    oidc_data: OIDCLogin,
    request: Request,
    language: str = Depends(get_request_language),
    session: AsyncSession = Depends(get_db)
):
    """
    OIDC回调处理
    
    Args:
        oidc_data: OIDC数据
        session: 异步数据库会话
    
    Returns:
        登录结果
    """
    try:
        # 获取客户端IP
        client_ip = request.client.host
        
        result = await OAuthService.handle_oidc_login(
            session=session,
            issuer=oidc_data.issuer,
            code=oidc_data.code,
            state=oidc_data.state,
            client_ip=client_ip
        )
        
        return result
        
    except Exception as e:
        logging.error(f"OIDC登录失败: {e}")
        raise HTTPException(status_code=400, detail=I18nService.get_error_message("oidc_login_failed", language))

@router.get("/oidc/discover/{issuer:path}")
async def oidc_discover(
    issuer: str,
    language: str = Depends(get_request_language)
):
    """
    发现OIDC配置
    
    Args:
        issuer: OIDC发行者URL
    
    Returns:
        OIDC配置信息
    """
    try:
        config = await OAuthService.discover_oidc_config(issuer)
        
        if config:
            return {
                "issuer": issuer,
                "config": config
            }
        else:
            raise HTTPException(status_code=404, detail=I18nService.get_error_message("oidc_config_discovery_failed", language))
            
    except Exception as e:
        logging.error(f"OIDC配置发现失败: {e}")
        raise HTTPException(status_code=500, detail=I18nService.get_error_message("server_error", language)) 