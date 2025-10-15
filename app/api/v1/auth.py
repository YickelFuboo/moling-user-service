import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemes.auth import (
    LoginResponse, RefreshTokenRequest, RefreshTokenResponse,
    PasswordLogin, SmsLogin, EmailLogin,
    VerificationCodeRequest, VerificationCodeResponse
)   
from app.schemes.common import BaseResponse 
from app.infrastructure.database.factory import get_db
from app.models.user import User
from app.services.auth_mgmt.auth_service import AuthService
from app.services.auth_mgmt.verify_code_service import VerifyCodeService
from app.services.common.email_service import EmailService
from app.api.deps import get_current_active_user, oauth2_scheme, get_request_language
from app.constants.common import VERIFICATION_CODE_EXPIRE_MINUTES
from app.services.common.i18n_service import I18nService


router = APIRouter()


@router.post("/login/password", response_model=LoginResponse)
async def login_with_password(
    login_data: PasswordLogin,
    request: Request,
    language: str = Depends(get_request_language),
    session: AsyncSession = Depends(get_db)
):
    """密码登录"""
    try:
        client_ip = request.client.host if request.client else None
        return await AuthService.login_with_password(session, login_data, client_ip)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )


@router.post("/login/sms", response_model=LoginResponse)
async def login_with_sms(
    login_data: SmsLogin,
    request: Request,
    language: str = Depends(get_request_language),
    session: AsyncSession = Depends(get_db)
):
    """短信验证码登录"""
    try:
        client_ip = request.client.host if request.client else None
        return await AuthService.login_with_sms(session, login_data, client_ip)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )


@router.post("/login/email", response_model=LoginResponse)
async def login_with_email(
    login_data: EmailLogin,
    request: Request,
    language: str = Depends(get_request_language),
    session: AsyncSession = Depends(get_db)
):
    """邮箱验证码登录"""
    try:
        client_ip = request.client.host if request.client else None
        return await AuthService.login_with_email(session, login_data, client_ip)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    language: str = Depends(get_request_language),
    session: AsyncSession = Depends(get_db)
):
    """刷新访问令牌"""
    try:
        result = await AuthService.refresh_token(session, refresh_data.refresh_token)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )

@router.post("/logout", response_model=BaseResponse)
async def logout(
    current_user: User = Depends(get_current_active_user),
    token: str = Depends(oauth2_scheme),
    language: str = Depends(get_request_language),
    session: AsyncSession = Depends(get_db)
):
    """用户登出"""
    try:
        result = await AuthService.logout(session, current_user, token)
        
        if result["success"]:
            return BaseResponse(
                success=True,
                message=result["message"],
                data={
                    "user_id": result["user_id"],
                    "user_name": result["user_name"]
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )

@router.post("/send-verification-code", response_model=VerificationCodeResponse)
async def send_verification_code(
    request_data: VerificationCodeRequest,
    request: Request,
    language: str = Depends(get_request_language),
    session: AsyncSession = Depends(get_db)
):
    """发送验证码"""
    try:
        # 获取客户端信息
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        if request_data.code_type == "sms":
            # 发送短信验证码
            success = await VerifyCodeService.send_sms_verification_code(
                phone=request_data.identifier,
                ip_address=client_ip,
                user_agent=user_agent
            )
            if success:
                return VerificationCodeResponse(
                    success=True,
                    message=I18nService.get_success_message("sms_verification_code_sent_success", language),
                    expires_in=VERIFICATION_CODE_EXPIRE_MINUTES * 60  # 转换为秒
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=I18nService.get_error_message("sms_verification_code_sent_failed", language)
                )
        elif request_data.code_type == "email":
            # 发送邮箱验证码
            success = await VerifyCodeService.send_email_verification_code(
                email=request_data.identifier,
                ip_address=client_ip,
                user_agent=user_agent,
                language=request_data.language
            )
            
            if success:
                return VerificationCodeResponse(
                    success=True,
                    message=I18nService.get_success_message("email_verification_code_sent_success", language),
                    expires_in=VERIFICATION_CODE_EXPIRE_MINUTES * 60  # 转换为秒
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=I18nService.get_error_message("email_verification_code_sent_failed", language)
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=I18nService.get_error_message("unsupported_verification_code_type", language)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        ) 

 