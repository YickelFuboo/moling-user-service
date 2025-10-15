import logging
from typing import Dict, Any


class I18nService:
    """国际化消息服务"""
    
    # 消息字典
    MESSAGES = {
        "zh-CN": {
            # 通用消息
            "success": "操作成功",
            "failed": "操作失败",
            "error": "发生错误",
            "not_found": "未找到",
            "unauthorized": "未授权",
            "forbidden": "权限不足",
            "validation_error": "数据验证失败",
            "server_error": "服务器内部错误",
            
            # 用户相关
            "user_created": "用户创建成功",
            "user_updated": "用户信息更新成功",
            "user_deleted": "用户删除成功",
            "user_not_found": "用户不存在",
            "user_already_exists": "用户已存在",
            "user_disabled": "用户账户已被禁用",
            "invalid_credentials": "用户名或密码错误",
            "login_success": "登录成功",
            "logout_success": "退出登录成功",
            "registration_success": "注册成功",
            "password_changed": "密码修改成功",
            "email_verified": "邮箱验证成功",
            "phone_verified": "手机号验证成功",
            
            # 角色权限相关
            "role_created": "角色创建成功",
            "role_updated": "角色更新成功",
            "role_deleted": "角色删除成功",
            "role_not_found": "角色不存在",
            "role_already_exists": "角色已存在",
            "permission_created": "权限创建成功",
            "permission_updated": "权限更新成功",
            "permission_deleted": "权限删除成功",
            "permission_not_found": "权限不存在",
            "permission_denied": "权限不足",
            
            # 语言相关
            "language_changed": "语言切换成功",
            "language_reset": "语言重置成功",
            "unsupported_language": "不支持的语言",
            "get_languages_success": "获取支持的语言列表成功",
            "get_current_language_success": "获取当前语言成功",
            
            # 验证码相关
            "verification_code_sent": "验证码已发送",
            "verification_code_invalid": "验证码无效",
            "verification_code_expired": "验证码已过期",
            "verification_code_used": "验证码已使用",
            
            # 文件相关
            "file_uploaded": "文件上传成功",
            "file_deleted": "文件删除成功",
            "file_not_found": "文件不存在",
            "file_too_large": "文件过大",
            "invalid_file_type": "无效的文件类型",
            
            # OAuth相关
            "oauth_login_success": "第三方登录成功",
            "oauth_provider_not_found": "未找到OAuth提供商",
            "oauth_token_invalid": "OAuth令牌无效",
            "oauth_user_info_failed": "获取OAuth用户信息失败",
            
            # 系统相关
            "service_healthy": "服务运行正常",
            "service_unhealthy": "服务不健康",
            "maintenance_mode": "系统维护中",
            "rate_limit_exceeded": "请求频率过高",
        },
        "en-US": {
            # Common messages
            "success": "Operation successful",
            "failed": "Operation failed",
            "error": "An error occurred",
            "not_found": "Not found",
            "unauthorized": "Unauthorized",
            "forbidden": "Forbidden",
            "validation_error": "Validation error",
            "server_error": "Internal server error",
            
            # User related
            "user_created": "User created successfully",
            "user_updated": "User updated successfully",
            "user_deleted": "User deleted successfully",
            "user_not_found": "User not found",
            "user_already_exists": "User already exists",
            "user_disabled": "User account is disabled",
            "invalid_credentials": "Invalid username or password",
            "login_success": "Login successful",
            "logout_success": "Logout successful",
            "registration_success": "Registration successful",
            "password_changed": "Password changed successfully",
            "email_verified": "Email verified successfully",
            "phone_verified": "Phone number verified successfully",
            
            # Role and permission related
            "role_created": "Role created successfully",
            "role_updated": "Role updated successfully",
            "role_deleted": "Role deleted successfully",
            "role_not_found": "Role not found",
            "role_already_exists": "Role already exists",
            "permission_created": "Permission created successfully",
            "permission_updated": "Permission updated successfully",
            "permission_deleted": "Permission deleted successfully",
            "permission_not_found": "Permission not found",
            "permission_denied": "Permission denied",
            
            # Language related
            "language_changed": "Language changed successfully",
            "language_reset": "Language reset successfully",
            "unsupported_language": "Unsupported language",
            "get_languages_success": "Get supported languages successfully",
            "get_current_language_success": "Get current language successfully",
            
            # Verification code related
            "verification_code_sent": "Verification code sent",
            "verification_code_invalid": "Invalid verification code",
            "verification_code_expired": "Verification code expired",
            "verification_code_used": "Verification code already used",
            
            # File related
            "file_uploaded": "File uploaded successfully",
            "file_deleted": "File deleted successfully",
            "file_not_found": "File not found",
            "file_too_large": "File too large",
            "invalid_file_type": "Invalid file type",
            
            # OAuth related
            "oauth_login_success": "OAuth login successful",
            "oauth_provider_not_found": "OAuth provider not found",
            "oauth_token_invalid": "Invalid OAuth token",
            "oauth_user_info_failed": "Failed to get OAuth user info",
            
            # System related
            "service_healthy": "Service is healthy",
            "service_unhealthy": "Service is unhealthy",
            "maintenance_mode": "System under maintenance",
            "rate_limit_exceeded": "Rate limit exceeded",
        }
    }
    
    
    @staticmethod
    def get_message(key: str, language: str = "zh-CN", **kwargs) -> str:
        """
        获取国际化消息
        
        Args:
            key: 消息键
            language: 语言代码
            **kwargs: 格式化参数
            
        Returns:
            str: 格式化后的消息
        """
        try:
            # 获取消息字典
            messages = I18nService.MESSAGES.get(language, I18nService.MESSAGES["zh-CN"])
            
            # 获取消息
            message = messages.get(key, key)
            
            # 如果有格式化参数，进行格式化
            if kwargs:
                try:
                    message = message.format(**kwargs)
                except (KeyError, ValueError) as e:
                    logging.warning(f"消息格式化失败: {key}, 语言: {language}, 错误: {e}")
                    # 如果格式化失败，返回原始消息
                    pass
            
            return message
            
        except Exception as e:
            logging.error(f"获取国际化消息失败: {key}, 语言: {language}, 错误: {e}")
            return key
    
    @staticmethod
    def get_error_message(error_type: str, language: str = "zh-CN", **kwargs) -> str:
        """
        获取错误消息
        
        Args:
            error_type: 错误类型
            language: 语言代码
            **kwargs: 格式化参数
            
        Returns:
            str: 错误消息
        """
        return I18nService.get_message(error_type, language, **kwargs)
    
    @staticmethod
    def get_success_message(success_type: str, language: str = "zh-CN", **kwargs) -> str:
        """
        获取成功消息
        
        Args:
            success_type: 成功类型
            language: 语言代码
            **kwargs: 格式化参数
            
        Returns:
            str: 成功消息
        """
        return I18nService.get_message(success_type, language, **kwargs) 