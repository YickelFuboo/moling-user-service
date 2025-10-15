import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from app.config.settings import settings


class EmailService:
    """邮件服务类"""
    
    @staticmethod
    async def send_email(
        to_emails: List[str],
        subject: str,
        content: str,
        content_type: str = "html",
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None
    ) -> bool:
        """
        发送邮件
        
        Args:
            to_emails: 收件人邮箱列表
            subject: 邮件主题
            content: 邮件内容
            content_type: 内容类型 (html/plain)
            cc_emails: 抄送邮箱列表
            bcc_emails: 密送邮箱列表
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = settings.email_from
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # 添加邮件内容
            msg.attach(MIMEText(content, content_type, 'utf-8'))
            
            # 连接SMTP服务器
            if settings.email_use_tls:
                server = smtplib.SMTP(settings.email_host, settings.email_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(settings.email_host, settings.email_port)
            
            # 登录
            server.login(settings.email_username, settings.email_password)
            
            # 发送邮件
            all_recipients = to_emails.copy()
            if cc_emails:
                all_recipients.extend(cc_emails)
            if bcc_emails:
                all_recipients.extend(bcc_emails)
            
            server.sendmail(settings.email_from, all_recipients, msg.as_string())
            server.quit()
            
            logging.info(f"邮件发送成功: {subject} -> {to_emails}")
            return True
            
        except Exception as e:
            logging.error(f"邮件发送失败: {e}")
            return False
    
    @staticmethod
    async def send_verification_email(email: str, verification_code: str, language: str = "zh-CN") -> bool:
        """
        发送验证码邮件
        
        Args:
            email: 收件人邮箱
            verification_code: 验证码
            language: 语言
            
        Returns:
            bool: 发送是否成功
        """
        if language == "zh-CN":
            subject = "验证码 - 用户服务"
            content = f"""
            <html>
            <body>
                <h2>验证码</h2>
                <p>您的验证码是: <strong>{verification_code}</strong></p>
                <p>验证码有效期为5分钟，请及时使用。</p>
                <p>如果这不是您的操作，请忽略此邮件。</p>
            </body>
            </html>
            """
        else:
            subject = "Verification Code - User Service"
            content = f"""
            <html>
            <body>
                <h2>Verification Code</h2>
                <p>Your verification code is: <strong>{verification_code}</strong></p>
                <p>The verification code is valid for 5 minutes, please use it in time.</p>
                <p>If this is not your operation, please ignore this email.</p>
            </body>
            </html>
            """
        
        return await EmailService.send_email([email], subject, content, "html")
    
    @staticmethod
    async def send_welcome_email(email: str, username: str, language: str = "zh-CN") -> bool:
        """
        发送欢迎邮件
        
        Args:
            email: 收件人邮箱
            username: 用户名
            language: 语言
            
        Returns:
            bool: 发送是否成功
        """
        if language == "zh-CN":
            subject = "欢迎注册 - 用户服务"
            content = f"""
            <html>
            <body>
                <h2>欢迎注册</h2>
                <p>亲爱的 {username}，</p>
                <p>感谢您注册我们的用户服务！</p>
                <p>您的账户已经创建成功，现在可以开始使用我们的服务了。</p>
                <p>如有任何问题，请随时联系我们。</p>
            </body>
            </html>
            """
        else:
            subject = "Welcome - User Service"
            content = f"""
            <html>
            <body>
                <h2>Welcome</h2>
                <p>Dear {username},</p>
                <p>Thank you for registering with our user service!</p>
                <p>Your account has been created successfully, and you can now start using our services.</p>
                <p>If you have any questions, please feel free to contact us.</p>
            </body>
            </html>
            """
        
        return await EmailService.send_email([email], subject, content, "html") 

    @staticmethod
    async def send_password_email(email: str, password: str, language: str = "zh-CN") -> bool:
        """
        发送密码邮件
        
        Args:
            email: 收件人邮箱
            password: 密码
            language: 语言
            
        Returns:
            bool: 发送是否成功
        """
        if language == "zh-CN":
            subject = "您的账户密码 - 用户服务"
            content = f"""
            <html>
            <body>
                <h2>您的账户密码</h2>
                <p>您好！</p>
                <p>您的账户密码是: <strong>{password}</strong></p>
                <p>请妥善保管此密码，并在首次登录后立即修改密码以确保账户安全。</p>
                <p>如果这不是您本人的操作，请忽略此邮件。</p>
                <p>祝好！</p>
            </body>
            </html>
            """
        else:
            subject = "Your Account Password - User Service"
            content = f"""
            <html>
            <body>
                <h2>Your Account Password</h2>
                <p>Hello!</p>
                <p>Your account password is: <strong>{password}</strong></p>
                <p>Please keep this password safe and change it immediately after your first login to ensure account security.</p>
                <p>If this is not your operation, please ignore this email.</p>
                <p>Best regards!</p>
            </body>
            </html>
            """
        
        return await EmailService.send_email([email], subject, content, "html") 