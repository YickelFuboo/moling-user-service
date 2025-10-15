from typing import Optional
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.database.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """用户模型"""
    __tablename__ = "users"
    
    # 基础信息
    id = Column(String(36), primary_key=True, index=True)
    user_name = Column(String(50), unique=True, index=True, nullable=False)
    user_full_name = Column(String(100), nullable=True)
    avatar = Column(String(255), nullable=True)  # 头像文件ID
    
    # 登录凭证
    email = Column(String(100), unique=True, index=True, nullable=True)  # 允许为空，支持第三方登录
    phone = Column(String(20), unique=True, index=True, nullable=True)   # 手机号
    hashed_password = Column(String(255), nullable=True)  # 允许为空，支持第三方登录
    
    # 注册信息
    registration_method = Column(String(20), default="email")  # email, phone, github, google, wechat, alipay
    
    # 第三方登录信息
    github_id = Column(String(100), unique=True, index=True, nullable=True)
    google_id = Column(String(100), unique=True, index=True, nullable=True)
    wechat_id = Column(String(100), unique=True, index=True, nullable=True)
    alipay_id = Column(String(100), unique=True, index=True, nullable=True)
    
    # 用户状态
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    
    # 用户偏好设置
    language = Column(String(10), default="en-US")  # 用户语言偏好：zh-CN, en-US
    
    # 登录记录
    last_login_at = Column(DateTime(timezone=True), nullable=True)  # 最后登录时间
    last_login_ip = Column(String(45), nullable=True)  # 最后登录IP
    
    # 关联关系
    user_roles = relationship("UserInRole", back_populates="user")
    files = relationship("FileMetadata", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, user_name={self.user_name}, email={self.email})>"


class FileMetadata(Base, TimestampMixin):
    """文件元数据模型"""
    __tablename__ = "file_metadata"
    
    # 基础信息
    id = Column(String(36), primary_key=True, index=True)
    file_id = Column(String(255), unique=True, index=True, nullable=False)  # 存储系统中的文件ID
    original_filename = Column(String(255), nullable=False)  # 原始文件名
    content_type = Column(String(100), nullable=False)  # MIME类型：image/jpeg, application/pdf等
    file_size = Column(Integer, nullable=False)  # 文件大小（字节）
    bucket_name = Column(String(50), default="default", nullable=False)  # 存储桶名称

    # 业务信息
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)  # 上传用户ID
    category = Column(String(20), default="general")  # 业务分类：avatar, document, image等
    
    # 关联关系
    user = relationship("User", back_populates="files")
    
    def __repr__(self):
        return f"<FileMetadata(id={self.id}, file_id={self.file_id}, filename={self.original_filename})>"
