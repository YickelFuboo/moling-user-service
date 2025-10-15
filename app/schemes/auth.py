from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# ==================== 登录相关模型 ====================

class PasswordLogin(BaseModel):
    """密码登录模型"""
    user_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str


class SmsLogin(BaseModel):
    """短信验证码登录模型"""
    phone: str
    verification_code: str


class EmailLogin(BaseModel):
    """邮箱验证码登录模型"""
    email: EmailStr
    verification_code: str


class OAuthLogin(BaseModel):
    """OAuth登录模型"""
    provider: str  # github, google, wechat, alipay
    code: str
    state: Optional[str] = None


class OIDCLogin(BaseModel):
    """OIDC登录模型"""
    issuer: str
    code: str
    state: Optional[str] = None


# ==================== 响应模型 ====================

class LoginResponse(BaseModel):
    """登录响应模型"""
    success: bool
    access_token: str
    refresh_token: str
    user: dict
    message: str


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """刷新令牌响应模型"""
    success: bool
    access_token: str
    refresh_token: str
    message: str


# ==================== 验证码相关模型 ====================

class VerificationCodeRequest(BaseModel):
    """验证码请求模型"""
    identifier: str  # 手机号或邮箱
    code_type: str  # "sms" 或 "email"


class VerificationCodeResponse(BaseModel):
    """验证码响应模型"""
    success: bool
    message: str
    expires_in: Optional[int] = None  # 验证码有效期（秒）


# ==================== OAuth相关模型 ====================

class OAuthBind(BaseModel):
    """OAuth绑定模型"""
    provider: str
    access_token: str
    user_id: str


class OAuthProviderInfo(BaseModel):
    """OAuth提供商信息"""
    provider: str
    display_name: str
    icon: str
    auth_url: str
    is_active: bool