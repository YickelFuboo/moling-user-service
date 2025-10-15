import json
import logging
import httpx
from typing import Optional
from app.config.settings import settings


class SMSService:
    """短信服务类"""
    
    @staticmethod
    async def send_sms(phone: str, template_params: dict, template_code: Optional[str] = None) -> bool:
        """
        发送短信
        
        Args:
            phone: 手机号
            template_params: 模板参数
            template_code: 模板代码（可选）
            
        Returns:
            bool: 发送是否成功
        """
        try:
            if settings.sms_provider.lower() == "aliyun":
                return await SMSService._send_aliyun_sms(phone, template_params, template_code)
            elif settings.sms_provider.lower() == "tencent":
                return await SMSService._send_tencent_sms(phone, template_params, template_code)
            else:
                logging.error(f"不支持的短信提供商: {settings.sms_provider}")
                return False
                
        except Exception as e:
            logging.error(f"短信发送失败: {e}")
            return False
    
    @staticmethod
    async def _send_aliyun_sms(phone: str, template_params: dict, template_code: Optional[str] = None) -> bool:
        """
        发送阿里云短信
        
        Args:
            phone: 手机号
            template_params: 模板参数
            template_code: 模板代码
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 这里应该使用阿里云SDK，这里简化处理
            # 实际项目中需要安装 aliyun-python-sdk-core 和 aliyun-python-sdk-dysmsapi
            
            url = "https://dysmsapi.aliyuncs.com"
            params = {
                "Action": "SendSms",
                "Version": "2017-05-25",
                "RegionId": "cn-hangzhou",
                "PhoneNumbers": phone,
                "SignName": settings.sms_sign_name,
                "TemplateCode": template_code or settings.sms_template_code,
                "TemplateParam": json.dumps(template_params)
            }
            
            # 这里简化处理，实际需要签名等认证
            # 实际项目中需要添加签名等认证逻辑
            logging.info(f"阿里云短信发送: {phone} -> {template_params}")
            return True
            
        except Exception as e:
            logging.error(f"阿里云短信发送失败: {e}")
            return False
    
    @staticmethod
    async def _send_tencent_sms(phone: str, template_params: dict, template_code: Optional[str] = None) -> bool:
        """
        发送腾讯云短信
        
        Args:
            phone: 手机号
            template_params: 模板参数
            template_code: 模板代码
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 这里应该使用腾讯云SDK，这里简化处理
            # 实际项目中需要安装 tencentcloud-sdk-python
            
            url = "https://sms.tencentcloudapi.com"
            params = {
                "Action": "SendSms",
                "Version": "2021-01-11",
                "Region": "ap-guangzhou",
                "PhoneNumberSet": [phone],
                "SmsSdkAppId": settings.sms_access_key_id,
                "SignName": settings.sms_sign_name,
                "TemplateId": template_code or settings.sms_template_code,
                "TemplateParamSet": list(template_params.values())
            }
            
            # 这里简化处理，实际需要签名等认证
            # 实际项目中需要添加签名等认证逻辑
            logging.info(f"腾讯云短信发送: {phone} -> {template_params}")
            return True
            
        except Exception as e:
            logging.error(f"腾讯云短信发送失败: {e}")
            return False
    
    @staticmethod
    async def send_verification_sms(phone: str, verification_code: str, language: str = "zh-CN") -> bool:
        """
        发送验证码短信
        
        Args:
            phone: 手机号
            verification_code: 验证码
            language: 语言标识 (zh-CN: 中文, en-US: 英文)
            
        Returns:
            bool: 发送是否成功
        """
        if language == "zh-CN":
            # 中文验证码短信
            template_params = {
                "code": verification_code,
                "expire_time": "5分钟",
                "message": f"您的验证码是: {verification_code}，验证码有效期为5分钟，请及时使用。如果这不是您的操作，请忽略此短信。"
            }
        else:
            # 英文验证码短信
            template_params = {
                "code": verification_code,
                "expire_time": "5 minutes",
                "message": f"Your verification code is: {verification_code}. The code is valid for 5 minutes, please use it in time. If this is not your operation, please ignore this message."
            }
        
        # 记录发送的短信内容
        logging.info(f"发送验证码短信到 {phone}: {template_params['message']}")
        
        return await SMSService.send_sms(phone, template_params)
    
    @staticmethod
    async def send_password_sms(phone: str, password: str, language: str = "zh-CN", 
                         app_name: str = "用户服务") -> bool:
        """
        发送密码短信
        
        Args:
            phone: 手机号
            password: 密码
            language: 语言标识 (zh-CN: 中文, en-US: 英文)
            app_name: 应用名称
            
        Returns:
            bool: 发送是否成功
        """
        if language == "zh-CN":
            # 中文密码短信
            template_params = {
                "password": password,
                "app_name": app_name,
                "message": f"欢迎注册{app_name}！您的随机密码是: {password}，请妥善保管并在首次登录后修改密码。如果这不是您的操作，请忽略此短信。"
            }
        else:
            # 英文密码短信
            template_params = {
                "password": password,
                "app_name": app_name,
                "message": f"Welcome to {app_name}! Your random password is: {password}. Please keep it safe and change it after your first login. If this is not your operation, please ignore this message."
            }
        
        # 记录发送的短信内容
        logging.info(f"发送密码短信到 {phone}: {template_params['message']}")
        
        return await SMSService.send_sms(phone, template_params) 