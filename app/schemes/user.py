from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator


class PasswordRegister(BaseModel):
    """密码注册模型"""
    user_name: str  # 用户名必填（覆盖父类的可选定义）
    password: str
    user_full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class SmsRegister(BaseModel):
    """短信注册模型"""
    phone: str
    verification_code: str


class EmailRegister(BaseModel):
    """邮箱注册模型"""
    email: EmailStr
    verification_code: str


"""用户响应模型"""
class UserResponse(BaseModel):
    """用户基础模型"""
    id: str
    user_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    user_full_name: Optional[str] = None
    avatar: Optional[str] = None
    language: str = "en-US"  # 用户语言偏好
    is_active: bool = True
    is_superuser: bool = False

    """用户响应模型"""
    email_verified: bool = False
    phone_verified: bool = False
    registration_method: str = "email"
    
    # 用户角色
    roles: List[str] = []
    
    # 第三方登录信息
    github_id: Optional[str] = None
    google_id: Optional[str] = None
    wechat_id: Optional[str] = None
    alipay_id: Optional[str] = None
    
    # 登录信息
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    
    # 时间戳
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """用户更新模型"""
    user_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    user_full_name: Optional[str] = None
    avatar: Optional[str] = None
    # 语言偏好通过专门的API管理，不在此处处理
    is_active: Optional[bool] = None
    # 验证码字段
    email_verification_code: Optional[str] = None
    phone_verification_code: Optional[str] = None


class UserPasswordChange(BaseModel):
    """用户密码修改模型"""
    current_password: str
    new_password: str
