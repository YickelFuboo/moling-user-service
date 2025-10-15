import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.infrastructure.database.factory import get_db
from app.services.permission_mgmt.role_service import RoleService
from app.schemes.common import BaseResponse, PaginationParams, PaginatedResponse
from app.api.deps import get_current_active_user, get_request_language
from app.models.user import User
from app.schemes.role import RoleBase
from app.services.common.i18n_service import I18nService

router = APIRouter()

@router.post("/", response_model=BaseResponse)
async def create_role(
    role_data: RoleBase,
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """创建角色"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=I18nService.get_error_message("permission_denied", language)
        )
    
    try:
        role = await RoleService.create_role(session, role_data)
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("role_created", language),
            data={"role_id": role.id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )

@router.get("/", response_model=PaginatedResponse)
async def get_roles(
    pagination: PaginationParams = Depends(),
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """获取角色列表"""
    try:
        result = await RoleService.get_roles(session, pagination)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )

@router.get("/{role_id}", response_model=BaseResponse)
async def get_role(
    role_id: str,
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """获取角色详情"""
    try:
        role = await RoleService.get_role_by_id(session, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=I18nService.get_error_message("role_not_found", language)
            )
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("role_get_success", language),
            data=role
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )

@router.put("/{role_id}", response_model=BaseResponse)
async def update_role(
    role_id: str,
    role_data: RoleBase,
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """更新角色"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=I18nService.get_error_message("permission_denied", language)
        )

    try:
        role = await RoleService.update_role(session, role_id, role_data)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=I18nService.get_error_message("role_not_found", language)
            )
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("role_updated", language),
            data={"role_id": role.id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )

@router.delete("/{role_id}", response_model=BaseResponse)
async def delete_role(
    role_id: str,
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """删除角色"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=I18nService.get_error_message("permission_denied", language)
        )
    
    try:
        success = await RoleService.delete_role(session, role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=I18nService.get_error_message("role_not_found", language)
            )
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("role_deleted", language),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )

@router.get("/{role_id}/users", response_model=BaseResponse)
async def get_role_users(
    role_id: str,
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """获取角色的用户列表"""
    try:
        role_service = RoleService(session)
        users = role_service.get_role_users(role_id)
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("role_users_get_success", language),
            data={"users": users}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )


@router.post("/{role_id}/users", response_model=BaseResponse)
async def add_users_to_role(
    role_id: str,
    user_ids: List[str],
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """为角色添加用户"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=I18nService.get_error_message("permission_denied", language)
        )
    
    try:
        role_service = RoleService(session)
        success = role_service.add_users_to_role(role_id, user_ids)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=I18nService.get_error_message("role_add_users_failed", language)
            )
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("role_add_users_success", language),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )


@router.delete("/{role_id}/users", response_model=BaseResponse)
async def remove_users_from_role(
    role_id: str,
    user_ids: List[str],
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """从角色移除用户"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=I18nService.get_error_message("permission_denied", language)
        )
    
    try:
        role_service = RoleService(session)
        success = role_service.remove_users_from_role(role_id, user_ids)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=I18nService.get_error_message("role_remove_users_failed", language)
            )
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("role_remove_users_success", language),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        ) 