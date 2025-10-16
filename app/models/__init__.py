# 1. 基础模型
from .base import Base, TimestampMixin

# 2. 核心模型（没有外键依赖）
from .user import User, FileMetadata
from .permission import Permission
from .role import Role

# 3. 关联模型（有外键依赖）
from .role import UserInRole
from .permission import RolePermission
from .tenant import Tenant

__all__ = [
    "Base",
    "TimestampMixin", 
    "User",
    "FileMetadata",
    "Permission",
    "Role",
    "UserInRole",
    "RolePermission",
    "Tenant"
]