from sqlalchemy import Column, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database.models.base import Base, TimestampMixin


class Permission(Base, TimestampMixin):
    """权限模型"""
    __tablename__ = "permissions"
    
    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    resource = Column(String(50), nullable=False)  # 资源名称
    action = Column(String(50), nullable=False)    # 操作类型：read, write, delete等

    # 状态
    is_active = Column(Boolean, default=True)
    
    # 关联关系
    role_permissions = relationship("RolePermission", back_populates="permission")
    
    def __repr__(self):
        return f"<Permission(id={self.id}, name={self.name}, resource={self.resource}, action={self.action})>"


class RolePermission(Base, TimestampMixin):
    """角色权限关联模型"""
    __tablename__ = "role_permissions"
    
    id = Column(String(36), primary_key=True, index=True)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    permission_id = Column(String(36), ForeignKey("permissions.id"), nullable=False)
    
    # 关联关系
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    
    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"

