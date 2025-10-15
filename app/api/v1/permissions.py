import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.infrastructure.database.factory import get_db
from app.services.permission_mgmt.permission_service import PermissionService
from app.schemes.common import BaseResponse, PaginationParams, PaginatedResponse
from app.schemes.permission import PermissionBase, PermissionResponse, RolePermissionAssign
from app.api.deps import get_current_active_user, get_request_language
from app.models.user import User
from app.services.common.i18n_service import I18nService

router = APIRouter()


@router.post("/", response_model=BaseResponse)
async def create_permission(
    permission_data: PermissionBase,
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """创建权限"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=I18nService.get_error_message("permission_denied", language)
        )
    
    try:
        permission = await PermissionService.create_permission(session, permission_data)
        
        # 转换为PermissionResponse格式
        permission_response = PermissionResponse(
            id=permission.id,
            name=permission.name,
            description=permission.description,
            resource=permission.resource,
            action=permission.action,
            is_active=permission.is_active,
            created_at=permission.created_at,
            updated_at=permission.updated_at
        )
        
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("permission_created", language),
            data=permission_response.dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )

@router.post("/assign", response_model=BaseResponse)
async def assign_permission_to_role(
    assign_data: RolePermissionAssign,
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """为角色分配权限"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=I18nService.get_error_message("permission_denied", language)
        )
    
    try:
        # 为每个权限ID分配权限
        success_count = 0
        for permission_id in assign_data.permission_ids:
            success = await PermissionService.assign_permission_to_role(session, assign_data.role_id, permission_id)
            if success:
                success_count += 1
        
        if success_count > 0:
            return BaseResponse(
                success=True,
                message=I18nService.get_success_message("permission_assigned", language),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=I18nService.get_error_message("permission_assign_failed", language)
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )

@router.get("/", response_model=PaginatedResponse)
async def get_permissions(
    pagination: PaginationParams = Depends(),
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """获取权限列表"""
    try:
        result = await PermissionService.get_permissions(session, pagination)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )

@router.get("/{permission_id}", response_model=BaseResponse)
async def get_permission(
    permission_id: str,
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """获取权限详情"""
    try:
        permission_service = PermissionService(session)
        permission = permission_service.get_permission_by_id(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=I18nService.get_error_message("permission_not_found", language)
            )
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("permission_get_success", language),
            data=permission.dict()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )

@router.get("/roles/{role_id}", response_model=BaseResponse)
async def get_role_permissions(
    role_id: str,
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """获取角色的权限列表"""
    try:
        permissions = await PermissionService.get_role_permissions(session, role_id)
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("role_permissions_get_success", language),
            data={"permissions": [p.dict() for p in permissions]}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        ) 

@router.get("/user/{user_id}", response_model=BaseResponse)
async def get_user_permissions(
    user_id: str,
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """获取用户权限"""
    try:
        permissions = await PermissionService.get_user_permissions(session, user_id)
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("user_permissions_get_success", language),
            data={"permissions": permissions}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )

@router.post("/check", response_model=BaseResponse)
async def check_user_permission(
    user_id: str,
    permission_name: str,
    language: str = Depends(get_request_language),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """检查用户权限"""
    try:
        permission_service = PermissionService(session)
        has_permission = permission_service.check_user_permission(user_id, permission_name)
        return BaseResponse(
            success=True,
            message=I18nService.get_success_message("permission_check_success", language),
            data={"has_permission": has_permission}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=I18nService.get_error_message("server_error", language)
        )