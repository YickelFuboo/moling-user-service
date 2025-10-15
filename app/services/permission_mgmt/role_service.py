import logging
import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from app.schemes.common import PaginationParams, PaginatedResponse
from app.models.role import Role, UserInRole
from app.models.user import User
from app.schemes.role import RoleBase
from app.schemes.user import UserResponse


class RoleService:
    """角色管理服务 - 静态方法版本"""
    
    @staticmethod
    async def create_role(session: AsyncSession, role_data: RoleBase) -> Role:
        """创建角色"""
        # 检查角色名是否已存在
        existing_role = await RoleService.get_role_by_name(session, role_data.name)
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色名已存在"
            )
        
        role = Role(
            id=str(uuid.uuid4()),
            name=role_data.name,
            description=role_data.description
        )
        
        session.add(role)
        await session.commit()
        await session.refresh(role)
        
        return role
    
    @staticmethod
    async def get_role_by_id(session: AsyncSession, role_id: str) -> Optional[Role]:
        """根据ID获取角色"""
        result = await session.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_role_by_name(session: AsyncSession, name: str) -> Optional[Role]:
        """根据名称获取角色"""
        result = await session.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_role(session: AsyncSession, name: str, description: str = None) -> Role:
        """获取或创建角色"""
        role = await RoleService.get_role_by_name(session, name)
        if not role:
            role_data = RoleBase(name=name, description=description)
            role = await RoleService.create_role(session, role_data)
        
        return role
    
    @staticmethod
    async def get_roles(session: AsyncSession, pagination: PaginationParams) -> PaginatedResponse:
        """获取角色列表"""
        query = select(Role)
        
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
                search_fields = ['name', 'description']
            
            # 根据指定字段进行搜索
            for field in search_fields:
                if field in ['name', 'role_name']:
                    search_conditions.append(Role.name.ilike(f"%{keyword}%"))
                elif field in ['description', 'desc', 'detail']:
                    search_conditions.append(Role.description.ilike(f"%{keyword}%"))
                elif field in ['id', 'role_id']:
                    # ID精确匹配
                    if keyword.isalnum():  # 确保是字母数字组合
                        search_conditions.append(Role.id == keyword)
            
            # 应用搜索条件
            if search_conditions:
                query = query.where(or_(*search_conditions))
        
        # 计算总数
        count_result = await session.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar()
        
        # 分页
        paginated_query = query.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
        result = await session.execute(paginated_query)
        roles = result.scalars().all()
        
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        
        return PaginatedResponse(
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            items=roles
        )

    @staticmethod
    async def update_role(session: AsyncSession, role_id: str, role_data: RoleBase) -> Role:
        """更新角色"""
        role = await RoleService.get_role_by_id(session, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        if role_data.name is not None:
            # 检查新角色名是否已被其他角色使用
            result = await session.execute(
                select(Role).where(
                    Role.name == role_data.name,
                    Role.id != role_id
                )
            )
            existing_role = result.scalar_one_or_none()

            if existing_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="角色名已存在"
                )
            
            role.name = role_data.name
        
        if role_data.description is not None:
            role.description = role_data.description
        
        if role_data.is_active is not None:
            role.is_active = role_data.is_active
        
        await session.commit()
        await session.refresh(role)
        
        return role
    
    @staticmethod
    async def delete_role(session: AsyncSession, role_id: str) -> bool:
        """删除角色"""
        role = await RoleService.get_role_by_id(session, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 检查是否有用户使用该角色
        result = await session.execute(select(func.count()).select_from(UserInRole).where(UserInRole.role_id == role_id))
        user_count = result.scalar()
        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该角色正在被用户使用，无法删除"
            )
        
        # 删除角色
        await session.delete(role)
        await session.commit()
        
        return True
    
    @staticmethod
    async def get_role_users(session: AsyncSession, role_id: str) -> List[UserResponse]:
        """获取角色的用户列表"""
        
        result = await session.execute(select(UserInRole).where(UserInRole.role_id == role_id))
        user_roles = result.scalars().all()
        user_ids = [ur.user_id for ur in user_roles]
        result = await session.execute(select(User).where(User.id.in_(user_ids)))
        users = result.scalars().all()
        
        # 转换为UserResponse格式，过滤敏感信息
        user_responses = []
        for user in users:
            # 获取用户角色
            result = await session.execute(select(UserInRole).where(UserInRole.user_id == user.id))
            user_roles = result.scalars().all()
            role_ids = [ur.role_id for ur in user_roles]
            result = await session.execute(select(Role).where(Role.id.in_(role_ids)))
            roles = result.scalars().all()
            role_names = [role.name for role in roles]
            
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
                roles=role_names,
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
            user_responses.append(user_response)
        
        return user_responses
    
    @staticmethod
    async def add_users_to_role(session: AsyncSession, role_id: str, user_ids: List[str]) -> bool:
        """为角色添加用户"""
        try:
            # 检查角色是否存在
            role = await RoleService.get_role_by_id(session, role_id)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="角色不存在"
                )
            
            # 检查用户是否存在
            result = await session.execute(select(User).where(User.id.in_(user_ids)))
            users = result.scalars().all()
            if len(users) != len(user_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="部分用户不存在"
                )
            
            # 检查是否已经分配了该角色
            result = await session.execute(
                select(UserInRole).where(
                    UserInRole.role_id == role_id,
                    UserInRole.user_id.in_(user_ids)
                )
            )
            existing_user_roles = result.scalars().all()
            
            existing_user_ids = [ur.user_id for ur in existing_user_roles]
            new_user_ids = [uid for uid in user_ids if uid not in existing_user_ids]
            
            # 添加新的用户角色关联
            for user_id in new_user_ids:
                user_role = UserInRole(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    role_id=role_id
                )
                session.add(user_role)
            
            await session.commit()
            logging.info(f"为角色 {role.name} 添加了 {len(new_user_ids)} 个用户")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"为角色添加用户失败: {e}")
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="为角色添加用户失败"
            )
    
    @staticmethod
    async def remove_users_from_role(session: AsyncSession, role_id: str, user_ids: List[str]) -> bool:
        """从角色移除用户"""
        try:
            # 检查角色是否存在
            role = await RoleService.get_role_by_id(session, role_id)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="角色不存在"
                )
            
            # 删除用户角色关联
            result = await session.execute(
                select(UserInRole).where(
                    UserInRole.role_id == role_id,
                    UserInRole.user_id.in_(user_ids)
                )
            )
            user_roles_to_delete = result.scalars().all()
            deleted_count = len(user_roles_to_delete)
            
            for user_role in user_roles_to_delete:
                await session.delete(user_role)
            
            await session.commit()
            logging.info(f"从角色 {role.name} 移除了 {deleted_count} 个用户")
            return True
            
        except Exception as e:
            logging.error(f"从角色移除用户失败: {e}")
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="从角色移除用户失败"
            ) 