from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.database.models.base import Base, TimestampMixin


class Role(Base, TimestampMixin):
    """角色模型"""
    __tablename__ = "roles"
    
    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

    # 状态
    is_active = Column(Boolean, default=True)
    
    # 关联关系
    user_roles = relationship("UserInRole", back_populates="role")
    role_permissions = relationship("RolePermission", back_populates="role")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class UserInRole(Base, TimestampMixin):
    """用户角色关联模型"""
    __tablename__ = "user_roles"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    
    # 关联关系
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    
    def __repr__(self):
        return f"<UserInRole(user_id={self.user_id}, role_id={self.role_id})>" 