import secrets
import string
import bcrypt
from app.constants.common import (
    PASSWORD_MIN_LENGTH,
    PASSWORD_REQUIRE_UPPERCASE,
    PASSWORD_REQUIRE_LOWERCASE,
    PASSWORD_REQUIRE_DIGITS,
    PASSWORD_REQUIRE_SPECIAL_CHARS,
    BCRYPT_ROUNDS
)

class PasswordService:

    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        """
        生成随机密码
        
        Args:
            length: 密码长度，默认12位
            
        Returns:
            str: 生成的随机密码
        """
        # 确保包含所有必需的字符类型
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # 每种类型至少包含一个字符
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special_chars)
        ]
        
        # 填充剩余长度
        remaining_length = length - 4
        all_chars = lowercase + uppercase + digits + special_chars
        password.extend(secrets.choice(all_chars) for _ in range(remaining_length))
        
        # 打乱密码字符顺序
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        
        return ''.join(password_list)


    @staticmethod
    def check_password_strength(password: str) -> bool:
        """
        检查密码强度：密码必须不少于8位，且包含大小写字母、数字、特殊字符
        
        Args:
            password: 待检查的密码
            
        Returns:
            bool: 密码是否符合强度要求
        """
        if len(password) < PASSWORD_MIN_LENGTH:
            return False
        
        if PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            return False
        
        if PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            return False
        
        if PASSWORD_REQUIRE_DIGITS and not any(c.isdigit() for c in password):
            return False
        
        if PASSWORD_REQUIRE_SPECIAL_CHARS and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False
        
        return True


    @staticmethod
    def hash_password(password: str) -> str:
        """
        使用bcrypt对密码进行哈希处理
        
        Args:
            password: 原始密码
            
        Returns:
            str: bcrypt哈希后的密码
        """
        # 使用常量中定义的轮数
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')


    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        使用bcrypt验证密码
        
        Args:
            password: 待验证的密码
            hashed_password: bcrypt哈希后的密码
            
        Returns:
            bool: 密码是否正确
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False


