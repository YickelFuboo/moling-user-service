import logging
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.config import settings
from app.infrastructure.redis.factory import REDIS_CONN
from app.constants.common import (
    VERIFICATION_CODE_LENGTH,
    VERIFICATION_CODE_EXPIRE_MINUTES,
    VERIFICATION_CODE_MAX_ATTEMPTS
)
from app.services.common.email_service import EmailService
from app.services.common.sms_service import SMSService


class VerifyCodeService:
    """验证码服务类"""
    
    @staticmethod
    def _generate_verification_code(length: int = None) -> str:
        """生成验证码"""
        if length is None:
            length = VERIFICATION_CODE_LENGTH
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def _generate_redis_key(identifier: str, code_type: str, purpose: str) -> str:
        """生成Redis键"""
        return f"verification:{identifier}:{code_type}:{purpose}"
    
    @staticmethod
    async def _create_verification_data(identifier: str, code: str, code_type: str, 
                                purpose: str = "verification", ip_address: str = None, 
                                user_agent: str = None, expires_in_minutes: int = None) -> Dict[str, Any]:
        """创建验证码记录到Redis"""
        # 先使之前的验证码失效
        await VerifyCodeService._invalidate_previous_codes(identifier, code_type, purpose)
        
        # 使用默认过期时间
        if expires_in_minutes is None:
            expires_in_minutes = VERIFICATION_CODE_EXPIRE_MINUTES
        
        # 生成唯一ID
        verification_id = str(uuid.uuid4())
        
        # 创建验证码数据
        verification_data = {
            "id": verification_id,
            "identifier": identifier,
            "code": code,
            "code_type": code_type,
            "purpose": purpose,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(minutes=expires_in_minutes)).isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "attempts": 0,
            "is_used": False,
            "is_expired": False
        }
        
        # 生成Redis键
        redis_key = VerifyCodeService._generate_redis_key(identifier, code_type, purpose)
        
        # 存储到Redis，设置过期时间
        expire_seconds = expires_in_minutes * 60 + 300  # 额外5分钟缓冲
        success = await REDIS_CONN.set(redis_key, verification_data, expire=expire_seconds)
        
        if success:
            logging.info(f"创建验证码到Redis: {identifier}, 类型: {code_type}, 用途: {purpose}")
            return verification_data
        else:
            logging.error(f"创建验证码到Redis失败: {identifier}")
            return None
    
    @staticmethod
    async def _invalidate_previous_codes(identifier: str, code_type: str, purpose: str):
        """使之前的验证码失效"""
        try:
            # 生成Redis键
            redis_key = VerifyCodeService._generate_redis_key(identifier, code_type, purpose)
            
            # 直接删除之前的验证码（Redis会自动处理过期）
            await REDIS_CONN.delete(redis_key)
            logging.info(f"使之前的验证码失效: {identifier}")
        except Exception as e:
            logging.error(f"使之前的验证码失效失败: {e}")
    
    @staticmethod
    async def send_sms_verification_code(phone: str, purpose: str = "verification", 
                                 ip_address: str = None, user_agent: str = None,
                                 language: str = "zh-CN") -> bool:
        """发送短信验证码"""
        try:
            # 检查发送频率限制
            if not await VerifyCodeService._check_rate_limit(phone, "sms"):
                logging.warning(f"短信发送频率过高: {phone}")
                return False
            
            # 生成验证码
            code = VerifyCodeService._generate_verification_code()
            
            # 创建验证码记录
            verification_data = await VerifyCodeService._create_verification_data(
                identifier=phone,
                code=code,
                code_type="sms",
                purpose=purpose,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_in_minutes=VERIFICATION_CODE_EXPIRE_MINUTES
            )
            
            if not verification_data:
                logging.error(f"创建验证码记录失败: {phone}")
                return False
            
            # 根据配置的短信服务提供商发送短信
            success = await SMSService.send_verification_sms(
                phone=phone,
                verification_code=code,
                language=language  # 默认中文，可以通过参数传递
            )
            
            if success:
                logging.info(f"短信验证码发送成功: {phone}")
            else:
                # 发送失败，删除验证码记录
                redis_key = VerifyCodeService._generate_redis_key(phone, "sms", purpose)
                await REDIS_CONN.delete(redis_key)
                logging.error(f"短信验证码发送失败: {phone}")
            
            return success
                
        except Exception as e:
            logging.error(f"发送短信验证码失败: {e}")
            return False
    
    @staticmethod
    async def send_email_verification_code(email: str, purpose: str = "verification", 
                                   ip_address: str = None, user_agent: str = None, 
                                   language: str = "zh-CN") -> bool:
        """发送邮箱验证码"""
        try:
            # 检查发送频率限制
            if not await VerifyCodeService._check_rate_limit(email, "email"):
                logging.warning(f"邮件发送频率过高: {email}")
                return False
            
            # 生成验证码
            code = VerifyCodeService._generate_verification_code()
            
            # 创建验证码记录
            verification_data = await VerifyCodeService._create_verification_data(
                identifier=email,
                code=code,
                code_type="email",
                purpose=purpose,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_in_minutes=VERIFICATION_CODE_EXPIRE_MINUTES
            )
            
            if not verification_data:
                logging.error(f"创建验证码记录失败: {email}")
                return False
            
            # 发送验证码邮件
            success = await EmailService.send_verification_email(
                email=email,
                verification_code=code,
                language=language
            )
            
            if success:
                logging.info(f"邮箱验证码发送成功: {email}")
            else:
                # 发送失败，删除验证码记录
                redis_key = VerifyCodeService._generate_redis_key(email, "email", purpose)
                await REDIS_CONN.delete(redis_key)
                logging.error(f"邮箱验证码发送失败: {email}")
            
            return success
            
        except Exception as e:
            logging.error(f"发送邮箱验证码失败: {e}")
            return False
    
    @staticmethod
    async def verify_code(identifier: str, code: str, code_type: str, 
                   purpose: str = "verification") -> bool:
        """验证验证码"""
        try:
            # 生成Redis键
            redis_key = VerifyCodeService._generate_redis_key(identifier, code_type, purpose)
            verification_data = await REDIS_CONN.get(redis_key)
            
            if not verification_data:
                logging.warning(f"验证码不存在或已过期: {identifier}, 类型: {code_type}")
                return False
            
            # 检查是否已使用
            if verification_data.get("is_used", False):
                logging.warning(f"验证码已使用: {identifier}")
                return False
            
            # 检查是否已过期
            expires_at = datetime.fromisoformat(verification_data["expires_at"])
            if datetime.utcnow() > expires_at:
                logging.warning(f"验证码已过期: {identifier}")
                return False
            
            # 增加尝试次数
            attempts = verification_data.get("attempts", 0) + 1
            verification_data["attempts"] = attempts
            
            # 检查尝试次数限制
            if attempts > VERIFICATION_CODE_MAX_ATTEMPTS:
                verification_data["is_expired"] = True
                await REDIS_CONN.set(redis_key, verification_data)
                logging.warning(f"验证码尝试次数过多: {identifier}")
                return False
            
            # 验证验证码
            if verification_data["code"] == code:
                # 验证成功，标记为已使用
                verification_data["is_used"] = True
                await REDIS_CONN.set(redis_key, verification_data)
                logging.info(f"验证码验证成功: {identifier}")
                return True
            else:
                # 验证失败，更新尝试次数
                await REDIS_CONN.set(redis_key, verification_data)
                logging.warning(f"验证码错误: {identifier}, 尝试次数: {attempts}")
                return False
            
        except Exception as e:
            logging.error(f"验证验证码失败: {e}")
            return False
    
    @staticmethod
    async def _check_rate_limit(identifier: str, code_type: str) -> bool:
        """检查发送频率限制"""
        try:
            # 使用Redis计数器检查频率限制
            # 1分钟内限制
            one_minute_key = f"rate_limit:{identifier}:{code_type}:1min"
            one_minute_count = await REDIS_CONN.get(one_minute_key, 0)
            if one_minute_count >= 1:
                logging.warning(f"1分钟内频率限制: {identifier}")
                return False
            
            # 1小时内限制
            one_hour_key = f"rate_limit:{identifier}:{code_type}:1hour"
            one_hour_count = await REDIS_CONN.get(one_hour_key, 0)
            if one_hour_count >= 10:
                logging.warning(f"1小时内频率限制: {identifier}")
                return False
            
            # 更新计数器（使用原子操作）
            await REDIS_CONN.set(one_minute_key, 1, expire=60)  # 1分钟过期
            await REDIS_CONN.set(one_hour_key, one_hour_count + 1, expire=3600)   # 1小时过期
            
            return True
            
        except Exception as e:
            logging.error(f"检查频率限制失败: {e}")
            return True  # 出错时允许发送