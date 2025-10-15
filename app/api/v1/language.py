import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.factory import get_db
from app.models.user import User
from app.api.deps import get_current_active_user, get_request_language
from app.schemes.language import ChangeLanguageRequest
from app.schemes.common import BaseResponse
from app.constants.language import (
    get_supported_languages,
    is_supported_language,
    get_default_language
)
from app.services.auth_mgmt.jwt_service import JWTService
from app.services.common.i18n_service import I18nService


router = APIRouter()


@router.get("/supported", response_model=BaseResponse)
async def get_supported_languages_api(
    language: str = Depends(get_request_language)
):
    """
    获取支持的语言列表
    
    返回系统支持的所有语言信息
    """
    try:
        languages = get_supported_languages()
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("get_languages_success", language),
            data={"languages": languages}
        )
    except Exception as e:
        logging.error(f"获取支持的语言列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )


@router.post("/change", response_model=BaseResponse)
async def change_language(
    request: ChangeLanguageRequest,
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """
    切换用户语言偏好
    
    更新用户的语言设置，新的语言偏好将在下次登录时生效
    """
    try:
        # 验证语言是否支持
        if not is_supported_language(request.language):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=I18nService.get_error_message("unsupported_language", language, language=request.language)
            )
        
        # 更新用户语言偏好
        current_user.language = request.language
        await session.commit()
        
        logging.info(f"用户 {current_user.user_name} 切换语言为: {request.language}")
        
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("language_changed", language, language=request.language),
            data={
                "user_id": current_user.id,
                "username": current_user.user_name,
                "language": request.language
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"切换语言失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )


@router.get("/current", response_model=BaseResponse)
async def get_current_language(
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户的语言偏好
    
    返回用户当前设置的语言
    """
    try:
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("get_current_language_success", language),
            data={
                "user_id": current_user.id,
                "username": current_user.user_name,
                "language": current_user.language
            }
        )
        
    except Exception as e:
        logging.error(f"获取当前语言失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )


@router.post("/reset", response_model=BaseResponse)
async def reset_language(
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """
    重置用户语言偏好为默认语言
    
    将用户语言设置重置为系统默认语言（中文）
    """
    try:
        # 重置为默认语言
        default_language = get_default_language()
        current_user.language = default_language
        await session.commit()
        
        logging.info(f"用户 {current_user.user_name} 重置语言为默认语言")
        
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("language_reset", language, language=default_language),
            data={
                "user_id": current_user.id,
                "username": current_user.user_name,
                "language": current_user.language
            }
        )
        
    except Exception as e:
        logging.error(f"重置语言失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        ) 