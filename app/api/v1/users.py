import io
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.factory import get_db
from app.models.user import User
from app.api.deps import get_current_active_user, get_request_language
from app.schemes.common import PaginationParams, PaginatedResponse, BaseResponse
from app.schemes.user import UserUpdate, UserResponse, UserPasswordChange, PasswordRegister, SmsRegister, EmailRegister
from app.services.user_mgmt.user_service import UserService
from app.services.common.file_service import FileService, FileType
from app.services.common.i18n_service import I18nService


router = APIRouter()


@router.post("/register/password", response_model=BaseResponse)
async def register_with_password(
    register_data: PasswordRegister,
    language: str = Depends(get_request_language),
    session: AsyncSession = Depends(get_db)
):
    """密码注册"""
    try:
        user = await UserService.register_user_with_password(session, register_data)
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("registration_success", language),
            data={"user_id": user.id, "user_name": user.user_name}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )


@router.post("/register/sms", response_model=BaseResponse)
async def register_with_sms(
    register_data: SmsRegister,
    language: str = Depends(get_request_language),
    session: AsyncSession = Depends(get_db)
):
    """短信验证码注册"""
    try:
        user = await UserService.register_user_with_sms(session, register_data)
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("registration_success", language),
            data={"user_id": user.id, "user_name": user.user_name}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )


@router.post("/register/email", response_model=BaseResponse)
async def register_with_email(
    register_data: EmailRegister,
    language: str = Depends(get_request_language),
    session: AsyncSession = Depends(get_db)
):
    """邮箱验证码注册"""
    try:
        user = await UserService.register_user_with_email(session, register_data)
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("registration_success", language),
            data={"user_id": user.id, "user_name": user.user_name}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )

@router.get("/", response_model=PaginatedResponse[UserResponse])
async def get_users(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """获取用户列表"""
    try:
        result = await UserService.get_users(session, pagination)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}"
        )


@router.get("/{user_id}", response_model=BaseResponse)
async def get_user(
    user_id: str,
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """获取用户详情"""
    try:
        user = await UserService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=I18nService.get_error_message("user_not_found", language)
            )
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("user_updated", language),
            data=user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )


@router.put("/{user_id}", response_model=BaseResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """更新用户"""
    try:
        user = await UserService.update_user(session, user_id, user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=I18nService.get_error_message("user_not_found", language)
            )
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("user_updated", language),
            data={"user_id": user.id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )


@router.delete("/{user_id}", response_model=BaseResponse)
async def delete_user(
    user_id: str,
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """删除用户"""
    try:
        success = await UserService.delete_user(session, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=I18nService.get_error_message("user_not_found", language)
            )
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("user_deleted", language)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )


@router.post("/change-password", response_model=BaseResponse)
async def change_password(
    password_data: UserPasswordChange,
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """修改密码"""
    try:
        success = await UserService.change_password(
            session,
            current_user.id,
            password_data.old_password,
            password_data.new_password
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=I18nService.get_error_message("invalid_credentials", language)
            )
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("password_changed", language)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码修改失败: {str(e)}"
        )


@router.post("/upload-avatar", response_model=BaseResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """上传头像"""
    try:
        # 读取文件内容
        file_content = io.BytesIO()
        for chunk in file.file:
            file_content.write(chunk)
        file_content.seek(0)
        
        # 使用FileService上传头像
        file_id = await FileService.upload_file_by_type(
            file_data=file_content,
            filename=file.filename,
            file_type=FileType.AVATAR,
            user_id=current_user.id
        )
        
        if not file_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=I18nService.get_error_message("avatar_upload_failed", language)
            )
        
        # 获取头像访问URL
        avatar_url = await FileService.get_file_url(file_id, FileType.AVATAR)
        if not avatar_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=I18nService.get_error_message("avatar_url_generation_failed", language)
            )
        
        # 更新用户头像信息
        user = await UserService.get_user_by_id(session, current_user.id)
        if user:
            # 存储file_id到数据库
            user.avatar = file_id
            await session.commit()
        
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("avatar_uploaded", language),
            data={"avatar_url": avatar_url}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )


@router.get("/{user_id}/avatar", response_model=BaseResponse)
async def get_user_avatar(
    user_id: str,
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """获取用户头像URL"""
    try:
        user = await UserService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=I18nService.get_error_message("user_not_found", language)
            )
        
        if not user.avatar:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=I18nService.get_error_message("user_not_set_avatar", language)
            )
        
        # 获取头像URL
        avatar_url = await FileService.get_file_url(user.avatar, FileType.AVATAR)
        if not avatar_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=I18nService.get_error_message("avatar_url_generation_failed", language)
            )
        
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("avatar_get_success", language),
            data={"avatar_url": avatar_url}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )
