import logging
import io
import json
import os
import uuid
from typing import List, Optional
from fastapi import HTTPException, status, UploadFile
from PIL import Image
from sqlalchemy import or_, and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.schemes.common import PaginationParams, PaginatedResponse
from app.schemes.user import UserUpdate, UserResponse, PasswordRegister, SmsRegister, EmailRegister
from app.models.user import User
from app.models.role import Role, UserInRole
from app.constants.language import get_default_language
from app.constants.common import (
    PASSWORD_MIN_LENGTH,
    USERNAME_MIN_LENGTH,
    USERNAME_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    PHONE_MAX_LENGTH,
    NICKNAME_MAX_LENGTH
)
from app.services.common.email_service import EmailService
from app.services.common.sms_service import SMSService
from app.services.common.file_service import FileService, FileType
from app.services.auth_mgmt.password_service import PasswordService
from app.services.auth_mgmt.verify_code_service import VerifyCodeService
from app.services.permission_mgmt.role_service import RoleService

class UserService:
    """用户服务：注册、注销、修改"""
    
    @staticmethod
    async def register_user_with_password(session: AsyncSession, auth_data: PasswordRegister) -> User:
        """密码注册用户"""
        # 检查注册必备信息
        if not auth_data.user_name and not auth_data.email and not auth_data.phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名、邮箱或手机号不能为空"
            )
        
        # 验证用户名
        if auth_data.user_name:
            if len(auth_data.user_name) < USERNAME_MIN_LENGTH:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"用户名长度不能少于{USERNAME_MIN_LENGTH}个字符"
                )
            if len(auth_data.user_name) > USERNAME_MAX_LENGTH:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"用户名长度不能超过{USERNAME_MAX_LENGTH}个字符"
                )
        
        # 验证邮箱
        if auth_data.email:
            if len(auth_data.email) > EMAIL_MAX_LENGTH:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"邮箱长度不能超过{EMAIL_MAX_LENGTH}个字符"
                )
        
        # 验证手机号
        if auth_data.phone:
            if len(auth_data.phone) > PHONE_MAX_LENGTH:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"手机号长度不能超过{PHONE_MAX_LENGTH}个字符"
                )
        
        # 验证昵称
        if auth_data.user_full_name:
            if len(auth_data.user_full_name) > NICKNAME_MAX_LENGTH:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"昵称长度不能超过{NICKNAME_MAX_LENGTH}个字符"
                )
        
        # 检查密码内容合规要求
        if not PasswordService.check_password_strength(auth_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"密码长度至少为{PASSWORD_MIN_LENGTH}位，且包含大小写字母、数字、特殊字符"
            )

        # 检查用户名是否已存在
        result = await session.execute(select(User).where(
            (User.user_name == auth_data.user_name) | 
            (User.email == auth_data.email) |
            (User.phone == auth_data.phone)
        ))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名、邮箱或手机号已存在"
            )
        
        # 创建用户
        user = await UserService.create_user_with_default_role(session, {
            "user_name": auth_data.user_name,
            "email": auth_data.email,
            "phone": auth_data.phone,
            "hashed_password": PasswordService.hash_password(auth_data.password),
            "user_full_name": auth_data.user_full_name
        }, "password")
        
        # 发送欢迎邮件
        if user.email:
            await EmailService.send_welcome_email(
                email=user.email,
                username=user.user_name,
                language=user.language or "zh-CN"
            )
        
        return user
    
    @staticmethod
    async def register_user_with_sms(session: AsyncSession, auth_data: SmsRegister) -> User:
        """短信验证码注册用户"""
        # 验证短信验证码
        if not await VerifyCodeService.verify_code(auth_data.phone, auth_data.verification_code, "sms"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误或已过期"
            )
        
        # 检查手机号是否已存在
        result = await session.execute(select(User).where(User.phone == auth_data.phone))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="手机号已存在"
            )
        
        # 生成用户名（如果未提供，默认使用手机号）
        if auth_data.user_name:
            user_name = await UserService.generate_unique_username(session, auth_data.user_name)
        else:
            user_name = await UserService.generate_unique_username(session, auth_data.phone)
        
        # 生成随机密码
        random_password = PasswordService.generate_random_password(16)

        # 创建用户
        user = await UserService.create_user_with_default_role(session, {
            "user_name": user_name,
            "phone": auth_data.phone,
            "user_full_name": auth_data.user_full_name,
            "hashed_password": PasswordService.hash_password(random_password),
            "phone_verified": True  # 通过验证码注册的手机号自动验证
        }, "sms")
        
        # 通过短信发送密码给用户
        if not await SMSService.send_password_sms(auth_data.phone, random_password):
            logging.warning(f"无法通过短信发送密码给用户 {user.id}")
        
        logging.info(f"用户 {user.id} 通过短信注册，密码已发送到手机号: {auth_data.phone}")
        
        return user
    
    @staticmethod
    async def register_user_with_email(session: AsyncSession, auth_data: EmailRegister) -> User:
        """邮箱验证码注册用户"""
        # 验证邮箱验证码
        if not await VerifyCodeService.verify_code(auth_data.email, auth_data.verification_code, "email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误或已过期"
            )
        
        # 检查邮箱是否已存在
        result = await session.execute(select(User).where(User.email == auth_data.email))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        
        # 生成用户名（如果未提供，默认使用邮箱用户名）
        if auth_data.user_name:
            user_name = await UserService.generate_unique_username(session, auth_data.user_name)
        else:
            email_username = auth_data.email.split('@')[0]
            user_name = await UserService.generate_unique_username(session, email_username)
        
        # 生成随机密码
        random_password = PasswordService.generate_random_password(16)
        
        # 创建用户
        user = await UserService.create_user_with_default_role(session, {
            "user_name": user_name,
            "email": auth_data.email,
            "user_full_name": auth_data.user_full_name,
            "hashed_password": PasswordService.hash_password(random_password),
            "email_verified": True  # 通过验证码注册的邮箱自动验证
        }, "email")
        
        # 通过邮件发送密码给用户
        if not await EmailService.send_password_email(auth_data.email, random_password, language=user.language or "zh-CN"):
            logging.warning(f"无法通过邮件发送密码给用户 {user.id}")
        
        return user
    
    @staticmethod
    async def create_user(session: AsyncSession, user_data: dict, registration_method: str) -> User:
        """创建用户（不分配角色）"""
        
        user = User(
            id=str(uuid.uuid4()),
            user_name=user_data.get("user_name"),
            email=user_data.get("email", None),
            phone=user_data.get("phone", None),
            hashed_password=user_data.get("hashed_password", None),
            user_full_name=user_data.get("user_full_name", None),
            avatar=user_data.get("avatar", None),
            language=user_data.get("language", get_default_language()),  # 使用默认语言
            is_active=user_data.get("is_active", True),
            is_superuser=user_data.get("is_superuser", False),
            email_verified=user_data.get("email_verified", False),
            phone_verified=user_data.get("phone_verified", False),
            registration_method=registration_method,
            github_id=user_data.get("github_id", None),
            google_id=user_data.get("google_id", None),
            wechat_id=user_data.get("wechat_id", None),
            alipay_id=user_data.get("alipay_id", None),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        return user
    
    @staticmethod
    async def create_user_with_default_role(session: AsyncSession, user_data: dict, registration_method: str) -> User:
        """创建用户并分配默认角色"""
        
        # 创建用户
        user = await UserService.create_user(session, user_data, registration_method)
        
        # 获取或创建默认角色
        user_role = await RoleService.get_or_create_role(session, "user", "普通用户")
        
        # 分配默认角色
        user_in_role = UserInRole(
            id=str(uuid.uuid4()),
            user_id=user.id,
            role_id=user_role.id
        )
        session.add(user_in_role)
        await session.commit()
        
        return user
    
    @staticmethod
    async def generate_unique_username(session: AsyncSession, base_username: str) -> str:
        """生成唯一的用户名"""
        username = base_username
        counter = 1
        
        while True:
            result = await session.execute(select(User).where(User.user_name == username))
            existing_user = result.scalar_one_or_none()
            if not existing_user:
                break
            username = f"{base_username}{counter}"
            counter += 1
        
        return username 

    
    @staticmethod
    async def get_users(session: AsyncSession, pagination: PaginationParams) -> PaginatedResponse[UserResponse]:
        """获取用户列表"""
        query = select(User)
        
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
                search_fields = ['name', 'email', 'phone', 'full_name']
            
            # 根据指定字段进行搜索
            for field in search_fields:
                if field in ['name', 'username', 'user_name']:
                    search_conditions.append(User.user_name.ilike(f"%{keyword}%"))
                elif field in ['email', 'mail']:
                    search_conditions.append(User.email.ilike(f"%{keyword}%"))
                elif field in ['phone', 'mobile', 'telephone']:
                    search_conditions.append(User.phone.ilike(f"%{keyword}%"))
                elif field in ['full_name', 'real_name', 'display_name']:
                    search_conditions.append(User.user_full_name.ilike(f"%{keyword}%"))
                elif field in ['registration', 'reg_method', 'method']:
                    search_conditions.append(User.registration_method.ilike(f"%{keyword}%"))
                elif field in ['role', 'roles']:
                    # 角色搜索需要关联查询
                    role_subquery = select(UserInRole.user_id).join(Role).where(
                        Role.name.ilike(f"%{keyword}%")
                    ).subquery()
                    search_conditions.append(User.id.in_(role_subquery))
                elif field in ['status', 'active', 'is_active']:
                    # 状态搜索
                    if keyword.lower() in ['active', 'true', '1', '启用', '激活']:
                        search_conditions.append(User.is_active == True)
                    elif keyword.lower() in ['inactive', 'false', '0', '禁用', '停用']:
                        search_conditions.append(User.is_active == False)
                elif field in ['verified', 'verification']:
                    # 验证状态搜索
                    if keyword.lower() in ['verified', 'true', '1', '已验证']:
                        search_conditions.append(
                            or_(User.email_verified == True, User.phone_verified == True)
                        )
                    elif keyword.lower() in ['unverified', 'false', '0', '未验证']:
                        search_conditions.append(
                            and_(User.email_verified == False, User.phone_verified == False)
                        )
            
            # 应用搜索条件
            if search_conditions:
                query = query.where(or_(*search_conditions))
        
        # 计算总数
        count_result = await session.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar()
        
        # 分页
        paginated_query = query.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
        result = await session.execute(paginated_query)
        users = result.scalars().all()
        
        # 转换为响应模型
        user_responses = []
        for user in users:
            # 获取用户角色
            result = await session.execute(select(UserInRole).where(UserInRole.user_id == user.id))
            user_roles = result.scalars().all()
            role_ids = [ur.role_id for ur in user_roles]
            result = await session.execute(select(Role).where(Role.id.in_(role_ids)))
            roles = result.scalars().all()
            role_names = [role.name for role in roles]
            
            # 获取头像URL
            avatar_url = None
            if user.avatar:
                try:
                    avatar_url = await FileService.get_file_url(user.avatar, FileType.AVATAR)
                except Exception as e:
                    logging.warning(f"获取用户头像URL失败: {e}")
            
            user_response = UserResponse(
                id=user.id,
                user_name=user.user_name,
                email=user.email,
                phone=user.phone,
                user_full_name=user.user_full_name,
                avatar=avatar_url,  # 使用URL而不是file_id
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
            user_responses.append(user_response)
        
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        
        return PaginatedResponse(
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            items=user_responses
        )
    
    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_name_or_email(session: AsyncSession, username: str) -> Optional[User]:
        """根据用户名或邮箱获取用户"""
        result = await session.execute(select(User).where(
            (User.user_name == username) | (User.email == username)
        ))
        return result.scalar_one_or_none()
    
    
    @staticmethod
    async def update_user(session: AsyncSession, user_id: str, user_data: UserUpdate) -> User:
        """更新用户"""
        user = await UserService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 检查邮箱更新
        if user_data.email and user_data.email != user.email:
            # 验证邮箱验证码
            if not user_data.email_verification_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="更新邮箱需要提供验证码"
                )
            
            if not await VerifyCodeService.verify_code(user_data.email, user_data.email_verification_code, "email"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱验证码错误或已过期"
                )
            
            # 检查新邮箱是否已被其他用户使用
            result = await session.execute(select(User).where(
                User.email == user_data.email,
                User.id != user_id
            ))
            existing_user = result.scalar_one_or_none()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该邮箱已被其他用户使用"
                )
            
            user.email = user_data.email
            user.email_verified = True  # 通过验证码验证的邮箱自动标记为已验证
            logging.info(f"用户 {user_id} 更新邮箱为: {user_data.email}")
        
        # 检查手机号更新
        if user_data.phone and user_data.phone != user.phone:
            # 验证手机验证码
            if not user_data.phone_verification_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="更新手机号需要提供验证码"
                )
            
            if not await VerifyCodeService.verify_code(user_data.phone, user_data.phone_verification_code, "sms"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="手机验证码错误或已过期"
                )
            
            # 检查新手机号是否已被其他用户使用
            result = await session.execute(select(User).where(
                User.phone == user_data.phone,
                User.id != user_id
            ))
            existing_user = result.scalar_one_or_none()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该手机号已被其他用户使用"
                )
            
            user.phone = user_data.phone
            user.phone_verified = True  # 通过验证码验证的手机号自动标记为已验证
            logging.info(f"用户 {user_id} 更新手机号为: {user_data.phone}")
        
        # 更新其他字段（不需要验证码）
        if user_data.user_name:
            # 检查用户名是否已被其他用户使用
            result = await session.execute(select(User).where(
                User.user_name == user_data.user_name,
                User.id != user_id
            ))
            existing_user = result.scalar_one_or_none()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该用户名已被其他用户使用"
                )
            user.user_name = user_data.user_name
        
        if user_data.user_full_name:
            user.user_full_name = user_data.user_full_name
        
        if user_data.avatar:
            user.avatar = user_data.avatar
        
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        await session.commit()
        await session.refresh(user)
        
        return user
    
    @staticmethod
    async def delete_user(session: AsyncSession, user_id: str) -> bool:
        """删除用户"""
        try:
            user = await UserService.get_user_by_id(session, user_id)
            if not user:
                return False
            
            # 删除用户角色关联
            result = await session.execute(select(UserInRole).where(UserInRole.user_id == user_id))
            user_roles = result.scalars().all()
            for user_role in user_roles:
                await session.delete(user_role)
            
            # 删除用户
            await session.delete(user)
            await session.commit()
            
            return True
        except Exception as e:
            await session.rollback()
            return False
    
    @staticmethod
    async def change_password(session: AsyncSession, user_id: str, old_password: str, new_password: str) -> bool:
        """修改密码"""
        try:
            user = await UserService.get_user_by_id(session, user_id)
            if not user:
                return False
            
            # 验证旧密码
            if not PasswordService.verify_password(old_password, user.hashed_password):
                return False
            
            # 更新密码
            user.hashed_password = PasswordService.hash_password(new_password)
            await session.commit()
            
            return True
        except Exception as e:
            await session.rollback()
            return False
    
    
    @staticmethod
    async def get_avatar_url(session: AsyncSession, user_id: str) -> Optional[str]:
        """获取用户头像URL"""
        user = await UserService.get_user_by_id(session, user_id)
        if not user or not user.avatar:
            return None
        
        try:
            # 使用通用方法，指定文件类型
            return await FileService.get_file_url(user.avatar, FileType.AVATAR)
        except Exception as e:
            logging.error(f"获取头像URL失败: {e}")
            return None
