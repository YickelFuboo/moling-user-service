import logging
import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.sql.expression import true
from app.schemes.permission import PermissionBase, PermissionResponse
from app.schemes.common import PaginationParams, PaginatedResponse
from app.models.user import User
from app.models.role import Role, UserInRole
from app.models.permission import Permission, RolePermission


class PermissionService:
    """权限资源管理服务类"""

    @staticmethod
    async def create_permission(session: AsyncSession, permission_data: PermissionBase) -> Permission:
        """创建权限"""
        try:
            permission = Permission(
                id=str(uuid.uuid4()),
                name=permission_data.name,
                description=permission_data.description,
                resource=permission_data.resource,
                action=permission_data.action,
                is_active=True
            )
            
            session.add(permission)
            await session.commit()
            await session.refresh(permission)
            
            logging.info(f"创建权限成功: {permission.name}")
            return permission
        except Exception as e:
            logging.error(f"创建权限失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建权限失败"
            )
    
    @staticmethod
    async def assign_permission_to_role(session: AsyncSession, role_id: str, permission_id: str) -> bool:
        """为角色分配权限"""
        try:
            result = await session.execute(select(Role).where(Role.id == role_id))
            role = result.scalar_one_or_none()
            result = await session.execute(select(Permission).where(Permission.id == permission_id))
            permission = result.scalar_one_or_none()
            
            if not role or not permission:
                logging.error(f"角色或权限不存在: {role_id} 或 {permission_id}")
                return False
            
            # 检查是否已经分配
            result = await session.execute(
                select(RolePermission).where(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                logging.info(f"权限已分配给角色: {role_id} 或 {permission_id}")
                return True
            
            # 创建新的角色权限关联
            role_permission = RolePermission(
                id=str(uuid.uuid4()),
                role_id=role_id,
                permission_id=permission_id
            )
            
            session.add(role_permission)
            await session.commit()
            
            logging.info(f"为角色 {role.name} 分配权限 {permission.name}")
            return True
        except Exception as e:
            logging.error(f"分配权限失败: {e}")
            return False
    
    @staticmethod
    async def get_permissions(session: AsyncSession, pagination: PaginationParams) -> PaginatedResponse:
        """获取权限列表"""
        try:
            query = select(Permission)
            
            # 关键词搜索
            if pagination.keyword and len(pagination.keyword.strip()) >= 2:
                keyword = pagination.keyword.strip()
                search_conditions = []
                
                # 解析搜索字段
                search_fields = []
                if pagination.search_fields:
                    search_fields = [field.strip().lower() for field in pagination.search_fields.split(',')]
                
                # 如果没有指定搜索字段，使用默认字段
                if not search_fields:
                    search_fields = ['name', 'description', 'resource', 'action']
                
                # 根据指定字段进行搜索
                for field in search_fields:
                    if field in ['name', 'permission_name']:
                        search_conditions.append(Permission.name.ilike(f"%{keyword}%"))
                    elif field in ['description', 'desc', 'detail']:
                        search_conditions.append(Permission.description.ilike(f"%{keyword}%"))
                    elif field in ['resource', 'res']:
                        search_conditions.append(Permission.resource.ilike(f"%{keyword}%"))
                    elif field in ['action', 'act']:
                        search_conditions.append(Permission.action.ilike(f"%{keyword}%"))
                    elif field in ['id', 'permission_id']:
                        # ID精确匹配
                        if keyword.isalnum():  # 确保是字母数字组合
                            search_conditions.append(Permission.id == keyword)
                
                # 应用搜索条件
                if search_conditions:
                    query = query.where(or_(*search_conditions))
            
            # 计算总数
            count_result = await session.execute(select(func.count()).select_from(query.subquery()))
            total = count_result.scalar()
            
            # 分页
            paginated_query = query.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
            result = await session.execute(paginated_query)
            permissions = result.scalars().all()
            
            # 转换为PermissionResponse格式
            permission_responses = []
            for permission in permissions:
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
                permission_responses.append(permission_response)
            
            total_pages = (total + pagination.page_size - 1) // pagination.page_size
            
            return PaginatedResponse(
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
                total_pages=total_pages,
                items=permission_responses
            )
            
        except Exception as e:
            logging.error(f"获取权限列表失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取权限列表失败"
            )
    
    @staticmethod
    async def get_permission_by_id(session: AsyncSession, permission_id: str) -> Optional[PermissionResponse]:
        """根据ID获取权限"""
        try:
            result = await session.execute(select(Permission).where(Permission.id == permission_id))
            permission = result.scalar_one_or_none()
            if not permission:
                logging.error(f"权限不存在: {permission_id}")
                return None
            
            return PermissionResponse(
                id=permission.id,
                name=permission.name,
                description=permission.description,
                resource=permission.resource,
                action=permission.action,
                is_active=permission.is_active,
                created_at=permission.created_at,
                updated_at=permission.updated_at
            )
        except Exception as e:
            logging.error(f"获取权限详情失败: {e}")
            return None
    
    @staticmethod
    async def get_role_permissions(session: AsyncSession, role_id: str) -> List[PermissionResponse]:
        """获取角色的权限列表"""
        try:
            # 获取角色的权限关联
            result = await session.execute(select(RolePermission).where(RolePermission.role_id == role_id))
            role_permissions = result.scalars().all()
            permission_ids = [rp.permission_id for rp in role_permissions]
            
            # 获取权限详情
            result = await session.execute(select(Permission).where(Permission.id.in_(permission_ids)))
            permissions = result.scalars().all()
            
            # 转换为PermissionResponse格式
            permission_responses = []
            for permission in permissions:
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
                permission_responses.append(permission_response)
            
            return permission_responses
            
        except Exception as e:
            logging.error(f"获取角色权限失败: {e}")
            return [] 
    
    @staticmethod
    async def get_user_permissions(session: AsyncSession, user_id: str) -> List[PermissionResponse]:
        """获取用户所有权限"""
        try:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return []
            
            permissions = []
            # 获取用户角色关联
            result = await session.execute(select(UserInRole).where(UserInRole.user_id == user_id))
            user_roles = result.scalars().all()
            
            for user_role in user_roles:
                # 获取角色信息
                result = await session.execute(select(Role).where(Role.id == user_role.role_id))
                role = result.scalar_one_or_none()
                if role and role.is_active:
                    # 通过RolePermission关联获取权限
                    result = await session.execute(
                        select(RolePermission).where(RolePermission.role_id == role.id)
                    )
                    role_permissions = result.scalars().all()
                    
                    for role_permission in role_permissions:
                        result = await session.execute(
                            select(Permission).where(Permission.id == role_permission.permission_id)
                        )
                        permission = result.scalar_one_or_none()
                        if permission and permission.is_active:
                            permissions.append(PermissionResponse(
                                id=permission.id,
                                name=permission.name,
                                description=permission.description,
                                resource=permission.resource,
                                action=permission.action,
                                is_active=permission.is_active,
                                created_at=permission.created_at,
                                updated_at=permission.updated_at
                            ))
            
            return permissions
        except Exception as e:
            logging.error(f"获取用户权限失败: {e}")
            return []

    @staticmethod
    async def check_user_permission(session: AsyncSession, user_id: str, permission_name: str) -> bool:
        """检查用户是否有指定权限"""
        try:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return False
            
            # 获取用户角色
            result = await session.execute(select(UserInRole).where(UserInRole.user_id == user_id))
            user_roles = result.scalars().all()
            if not user_roles:
                return False
            
            # 检查角色权限
            for user_role in user_roles:
                result = await session.execute(select(Role).where(Role.id == user_role.role_id))
                role = result.scalar_one_or_none()
                if role and role.is_active:
                    # 通过RolePermission关联获取权限
                    result = await session.execute(
                        select(RolePermission).where(RolePermission.role_id == role.id)
                    )
                    role_permissions = result.scalars().all()
                    
                    for role_permission in role_permissions:
                        result = await session.execute(
                            select(Permission).where(Permission.id == role_permission.permission_id)
                        )
                        permission = result.scalar_one_or_none()
                        if permission and permission.is_active and permission.name == permission_name:
                            return True
            
            return False
        except Exception as e:
            logging.error(f"检查用户权限失败: {e}")
            return False