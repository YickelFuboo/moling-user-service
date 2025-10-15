import logging
import uuid
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemes.auth import (
    LoginResponse, RefreshTokenRequest, RefreshTokenResponse,
    PasswordLogin, SmsLogin, EmailLogin
)
from app.schemes.user import UserResponse
from app.models.user import User
from app.models.role import Role, UserInRole
from app.services.auth_mgmt.jwt_service import JWTService
from app.services.auth_mgmt.password_service import PasswordService
from app.services.auth_mgmt.verify_code_service import VerifyCodeService


class AuthService:
    """认证服务 - 负责用户认证、登录、注册等业务逻辑""" 
    
    @staticmethod
    async def login_with_password(session: AsyncSession, auth_data: PasswordLogin, client_ip: str = None) -> LoginResponse:
        """密码登录"""
        user = None
        
        # 根据提供的标识符进行认证
        if auth_data.user_name:
            user = await AuthService._authenticate_user_by_name(session, auth_data.user_name, auth_data.password)
        elif auth_data.email:
            user = await AuthService._authenticate_user_by_email(session, auth_data.email, auth_data.password)
        elif auth_data.phone:
            user = await AuthService._authenticate_user_by_phone(session, auth_data.phone, auth_data.password)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供用户名、邮箱或手机号"
            )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已被禁用"
            )
        
        return await AuthService.create_login_response(session, user, client_ip)
    
    @staticmethod
    async def login_with_sms(session: AsyncSession, auth_data: SmsLogin, client_ip: str = None) -> LoginResponse:
        """短信验证码登录"""
        user = await AuthService._authenticate_user_by_verification_code(
            session, auth_data.phone, auth_data.verification_code, "sms"
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="验证码错误或已过期"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已被禁用"
            )
        
        return await AuthService.create_login_response(session, user, client_ip)
    
    @staticmethod
    async def login_with_email(session: AsyncSession, auth_data: EmailLogin, client_ip: str = None) -> LoginResponse:
        """邮箱验证码登录"""
        user = await AuthService._authenticate_user_by_verification_code(
            session, auth_data.email, auth_data.verification_code, "email"
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="验证码错误或已过期"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已被禁用"
            )
        
        return await AuthService.create_login_response(session, user, client_ip)
    
    @staticmethod
    async def _authenticate_user_by_name(session: AsyncSession, username: str, password: str) -> Optional[User]:
        """验证用户（用户名 + 密码）"""
        result = await session.execute(select(User).where(User.user_name == username))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        if not PasswordService.verify_password(password, user.hashed_password):
            return None
        
        return user
    
    @staticmethod
    async def _authenticate_user_by_email(session: AsyncSession, email: str, password: str) -> Optional[User]:
        """验证用户（邮箱 + 密码）"""
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        if not PasswordService.verify_password(password, user.hashed_password):
            return None
        
        return user 
        
    @staticmethod
    async def _authenticate_user_by_phone(session: AsyncSession, phone: str, password: str) -> Optional[User]:
        """验证用户（手机号 + 密码）"""
        result = await session.execute(select(User).where(User.phone == phone))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        if not PasswordService.verify_password(password, user.hashed_password):
            return None
        
        return user
    
    @staticmethod
    async def _authenticate_user_by_verification_code(session: AsyncSession, identifier: str, code: str, code_type: str) -> Optional[User]:
        """验证用户（验证码登录）"""
        # 验证验证码
        if not await VerifyCodeService.verify_code(identifier, code, code_type):
            return None
        
        try:
            # 先尝试通过邮箱查找
            result = await session.execute(select(User).where(User.email == identifier))
            user = result.scalar_one_or_none()
            if user:
                return user
            
            # 再尝试通过手机号查找
            result = await session.execute(select(User).where(User.phone == identifier))
            user = result.scalar_one_or_none()
            return user
            
        except Exception as e:
            logging.error(f"根据标识符获取用户失败: {e}")
            return None
    
    @staticmethod
    async def create_login_response(session: AsyncSession, user: User, client_ip: str = None) -> LoginResponse:
        """创建登录响应（内部方法）"""
        # 更新登录信息
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = client_ip
        await session.commit()
        
        # 获取用户角色
        result = await session.execute(select(UserInRole).where(UserInRole.user_id == user.id))
        user_roles = result.scalars().all()
        role_ids = [ur.role_id for ur in user_roles]
        result = await session.execute(select(Role).where(Role.id.in_(role_ids)))
        roles = result.scalars().all()
        role_names = [role.name for role in roles]
        
        # 创建令牌
        token_data = {
            "sub": user.id, 
            "username": user.user_name, 
            "roles": role_names,
            "email": user.email,
            "phone": user.phone,
            "full_name": user.user_full_name,
            "language": user.language,  # 添加语言信息
            "is_superuser": user.is_superuser,
            "is_active": user.is_active
        }
        access_token = await JWTService.create_access_token(token_data)
        refresh_token = await JWTService.create_refresh_token(token_data)
        
        # 构建用户响应
        user_response = UserResponse(
            id=user.id,
            user_name=user.user_name,
            email=user.email,
            phone=user.phone,
            user_full_name=user.user_full_name,
            avatar=user.avatar,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            email_verified=user.email_verified,
            phone_verified=user.phone_verified,
            roles=role_names,  # 添加用户角色
            registration_method=user.registration_method,
            github_id=user.github_id,
            google_id=user.google_id,
            wechat_id=user.wechat_id,
            alipay_id=user.alipay_id,
            last_login_at=user.last_login_at,
            last_login_ip=user.last_login_ip,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return LoginResponse(
            success=True,
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_response.dict(),
            message="登录成功"
        )   
    
    @staticmethod
    async def refresh_token(session: AsyncSession, refresh_data: RefreshTokenRequest) -> RefreshTokenResponse:
        """刷新令牌"""
        try:
            payload = await JWTService.verify_token(refresh_data.refresh_token)
            user_id = payload.get("sub")
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的刷新令牌"
                )
            
            # 验证用户是否存在
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户不存在或已被禁用"
                )
            
            # 获取用户角色
            result = await session.execute(select(UserInRole).where(UserInRole.user_id == user.id))
            user_roles = result.scalars().all()
            role_ids = [ur.role_id for ur in user_roles]
            result = await session.execute(select(Role).where(Role.id.in_(role_ids)))
            roles = result.scalars().all()
            role_names = [role.name for role in roles]
            
            # 创建新令牌
            token_data = {
                "sub": user.id, 
                "username": user.user_name, 
                "roles": role_names,
                "email": user.email,
                "phone": user.phone,
                "full_name": user.user_full_name,
                "language": user.language,  # 添加语言信息
                "is_superuser": user.is_superuser,
                "is_active": user.is_active
            }
            new_access_token = await JWTService.create_access_token(token_data)
            new_refresh_token = await JWTService.create_refresh_token(token_data)
            
            return RefreshTokenResponse(
                success=True,
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                message="令牌刷新成功"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌失败"
            )
    
    @staticmethod
    async def logout(user: User, token: str) -> dict:
        """用户登出"""
        try:
            # 将当前token加入黑名单
            success = await JWTService.add_to_blacklist(token)
            
            if success:
                logging.info(f"用户 {user.user_name} 登出成功，token已加入黑名单")
                return {
                    "success": True,
                    "message": "登出成功",
                    "user_id": user.id,
                    "user_name": user.user_name
                }
            else:
                logging.warning(f"用户 {user.user_name} 登出失败，token加入黑名单失败")
                return {
                    "success": False,
                    "message": "登出失败",
                    "user_id": user.id,
                    "user_name": user.user_name
                }
                
        except Exception as e:
            logging.error(f"用户登出异常: {e}")
            return {
                "success": False,
                "message": f"登出异常: {str(e)}",
                "user_id": user.id,
                "user_name": user.user_name
            } 