import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

# 定义全局配置常量 - 直接使用固定值避免导入问题
APP_NAME = "moling-user-service"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Moling User Service"

# 获取项目根目录
try:
    PROJECT_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
except Exception:
    PROJECT_BASE_DIR = os.getcwd()

class Settings(BaseSettings):
    """应用配置类 - 平铺结构"""
    
    # =============================================================================
    # 应用基础配置
    # =============================================================================
    service_host: str = Field(default="0.0.0.0", description="服务主机地址", env="SERVICE_HOST")
    service_port: int = Field(default=8001, description="服务端口", env="SERVICE_PORT")
    debug: bool = Field(default=False, description="调试模式", env="DEBUG")
    app_log_level: str = Field(default="INFO", description="日志级别", env="APP_LOG_LEVEL")
    
    # =============================================================================
    # 数据库配置
    # =============================================================================
    database_type: str = Field(default="postgresql", description="数据库类型: postgresql 或 mysql", env="DATABASE_TYPE")
    db_name: str = Field(default="user_service", description="数据库名称", env="DB_NAME")
    db_pool_size: int = Field(default=10, description="连接池大小", env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, description="最大溢出连接数", env="DB_MAX_OVERFLOW")
    
    # PostgreSQL 配置
    postgresql_host: str = Field(default="localhost", description="PostgreSQL主机地址", env="POSTGRESQL_HOST")
    postgresql_port: int = Field(default=5432, description="PostgreSQL端口", env="POSTGRESQL_PORT")
    postgresql_user: str = Field(default="postgres", description="PostgreSQL用户名", env="POSTGRESQL_USER")
    postgresql_password: str = Field(default="your_password", description="PostgreSQL密码", env="POSTGRESQL_PASSWORD")
    
    # MySQL 配置
    mysql_host: str = Field(default="localhost", description="MySQL主机地址", env="MYSQL_HOST")
    mysql_port: int = Field(default=3306, description="MySQL端口", env="MYSQL_PORT")
    mysql_user: str = Field(default="root", description="MySQL用户名", env="MYSQL_USER")
    mysql_password: str = Field(default="your_password", description="MySQL密码", env="MYSQL_PASSWORD")
    
    # =============================================================================
    # 文件存储配置
    # =============================================================================
    storage_type: str = Field(default="minio", description="存储类型: minio, s3, local", env="STORAGE_TYPE")
    
    # MinIO 配置
    minio_endpoint: str = Field(default="localhost:9000", description="MinIO端点", env="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", description="MinIO访问密钥", env="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", description="MinIO秘密密钥", env="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="user-service", description="MinIO存储桶", env="MINIO_BUCKET")
    minio_secure: bool = Field(default=False, description="MinIO是否使用HTTPS", env="MINIO_SECURE")
    
    # S3 配置
    s3_endpoint: str = Field(default="", description="S3端点", env="S3_ENDPOINT")
    s3_endpoint_url: str = Field(default="", description="S3端点URL", env="S3_ENDPOINT_URL")
    s3_access_key: str = Field(default="", description="S3访问密钥", env="S3_ACCESS_KEY")
    s3_access_key_id: str = Field(default="", description="S3访问密钥ID", env="S3_ACCESS_KEY_ID")
    s3_secret_key: str = Field(default="", description="S3秘密密钥", env="S3_SECRET_KEY")
    s3_secret_access_key: str = Field(default="", description="S3秘密访问密钥", env="S3_SECRET_ACCESS_KEY")
    s3_bucket: str = Field(default="", description="S3存储桶", env="S3_BUCKET")
    s3_region: str = Field(default="us-east-1", description="S3区域", env="S3_REGION")
    s3_use_ssl: bool = Field(default=False, description="S3是否使用SSL", env="S3_USE_SSL")
    
    # 本地存储配置
    local_storage_path: str = Field(default="./uploads", description="本地存储路径", env="LOCAL_STORAGE_PATH")
    local_upload_dir: str = Field(default="./uploads", description="本地上传目录", env="LOCAL_UPLOAD_DIR")
    
    # Azure 配置
    azure_account_url: str = Field(default="", description="Azure账户URL", env="AZURE_ACCOUNT_URL")
    azure_sas_token: str = Field(default="", description="Azure SAS令牌", env="AZURE_SAS_TOKEN")
    azure_spn_account_url: str = Field(default="", description="Azure SPN账户URL", env="AZURE_SPN_ACCOUNT_URL")
    azure_spn_client_id: str = Field(default="", description="Azure SPN客户端ID", env="AZURE_SPN_CLIENT_ID")
    azure_spn_client_secret: str = Field(default="", description="Azure SPN客户端秘密", env="AZURE_SPN_CLIENT_SECRET")
    azure_spn_tenant_id: str = Field(default="", description="Azure SPN租户ID", env="AZURE_SPN_TENANT_ID")
    azure_spn_container_name: str = Field(default="", description="Azure SPN容器名称", env="AZURE_SPN_CONTAINER_NAME")
    
    # OSS 配置
    oss_access_key: str = Field(default="", description="OSS访问密钥", env="OSS_ACCESS_KEY")
    oss_secret_key: str = Field(default="", description="OSS秘密密钥", env="OSS_SECRET_KEY")
    oss_endpoint_url: str = Field(default="", description="OSS端点URL", env="OSS_ENDPOINT_URL")
    oss_region: str = Field(default="", description="OSS区域", env="OSS_REGION")
    oss_prefix_path: str = Field(default="", description="OSS前缀路径", env="OSS_PREFIX_PATH")
    
    # =============================================================================
    # Redis 配置
    # =============================================================================
    redis_host: str = Field(default="localhost", description="Redis主机地址", env="REDIS_HOST")
    redis_port: int = Field(default=6379, description="Redis端口", env="REDIS_PORT")
    redis_password: str = Field(default="", description="Redis密码", env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, description="Redis数据库编号", env="REDIS_DB")
    redis_max_connections: int = Field(default=10, description="Redis最大连接数", env="REDIS_MAX_CONNECTIONS")
    redis_socket_timeout: int = Field(default=5, description="Redis套接字超时时间(秒)", env="REDIS_SOCKET_TIMEOUT")
    redis_socket_connect_timeout: int = Field(default=5, description="Redis连接超时时间(秒)", env="REDIS_SOCKET_CONNECT_TIMEOUT")
    redis_retry_on_timeout: bool = Field(default=True, description="Redis超时重试", env="REDIS_RETRY_ON_TIMEOUT")
    redis_decode_responses: bool = Field(default=True, description="Redis自动解码响应", env="REDIS_DECODE_RESPONSES")
    redis_ssl: bool = Field(default=False, description="Redis是否使用SSL", env="REDIS_SSL")
    
    # =============================================================================
    # JWT 配置
    # =============================================================================
    jwt_secret_key: str = Field(default="your-secret-key", description="JWT密钥", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", description="JWT算法", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间(分钟)", env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, description="刷新令牌过期时间(天)", env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # =============================================================================
    # 邮件配置
    # =============================================================================
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP主机", env="SMTP_HOST")
    smtp_port: int = Field(default=587, description="SMTP端口", env="SMTP_PORT")
    smtp_username: str = Field(default="", description="SMTP用户名", env="SMTP_USERNAME")
    smtp_password: str = Field(default="", description="SMTP密码", env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, description="是否使用TLS", env="SMTP_USE_TLS")
    smtp_from_email: str = Field(default="", description="发件人邮箱", env="SMTP_FROM_EMAIL")
    
    # 邮件配置别名（兼容.env文件）
    email_host: str = Field(default="smtp.gmail.com", description="邮件主机", env="EMAIL_HOST")
    email_port: int = Field(default=587, description="邮件端口", env="EMAIL_PORT")
    email_username: str = Field(default="", description="邮件用户名", env="EMAIL_USERNAME")
    email_password: str = Field(default="", description="邮件密码", env="EMAIL_PASSWORD")
    email_use_tls: bool = Field(default=True, description="邮件是否使用TLS", env="EMAIL_USE_TLS")
    email_from: str = Field(default="", description="发件人", env="EMAIL_FROM")
    
    # =============================================================================
    # 短信配置
    # =============================================================================
    sms_provider: str = Field(default="", description="短信服务提供商", env="SMS_PROVIDER")
    sms_api_key: str = Field(default="", description="短信API密钥", env="SMS_API_KEY")
    sms_api_secret: str = Field(default="", description="短信API秘密", env="SMS_API_SECRET")
    sms_from_number: str = Field(default="", description="发件人号码", env="SMS_FROM_NUMBER")
    sms_access_key_id: str = Field(default="", description="短信访问密钥ID", env="SMS_ACCESS_KEY_ID")
    sms_access_key_secret: str = Field(default="", description="短信访问密钥秘密", env="SMS_ACCESS_KEY_SECRET")
    sms_sign_name: str = Field(default="", description="短信签名", env="SMS_SIGN_NAME")
    sms_template_code: str = Field(default="", description="短信模板代码", env="SMS_TEMPLATE_CODE")
    
    # =============================================================================
    # OAuth 配置
    # =============================================================================
    oauth_enabled: bool = Field(default=False, description="是否启用OAuth", env="OAUTH_ENABLED")
    oauth_base_url: str = Field(default="http://localhost:8001", description="OAuth基础URL", env="OAUTH_BASE_URL")
    
    github_client_id: str = Field(default="", description="GitHub客户端ID", env="GITHUB_CLIENT_ID")
    github_client_secret: str = Field(default="", description="GitHub客户端秘密", env="GITHUB_CLIENT_SECRET")
    github_redirect_uri: str = Field(default="", description="GitHub重定向URI", env="GITHUB_REDIRECT_URI")
    
    google_client_id: str = Field(default="", description="Google客户端ID", env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", description="Google客户端秘密", env="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(default="", description="Google重定向URI", env="GOOGLE_REDIRECT_URI")
    
    # 微信配置
    wechat_app_id: str = Field(default="", description="微信应用ID", env="WECHAT_APP_ID")
    wechat_app_secret: str = Field(default="", description="微信应用秘密", env="WECHAT_APP_SECRET")
    wechat_redirect_uri: str = Field(default="", description="微信重定向URI", env="WECHAT_REDIRECT_URI")
    
    # 支付宝配置
    alipay_app_id: str = Field(default="", description="支付宝应用ID", env="ALIPAY_APP_ID")
    alipay_private_key: str = Field(default="", description="支付宝私钥", env="ALIPAY_PRIVATE_KEY")
    alipay_public_key: str = Field(default="", description="支付宝公钥", env="ALIPAY_PUBLIC_KEY")
    alipay_redirect_uri: str = Field(default="", description="支付宝重定向URI", env="ALIPAY_REDIRECT_URI")
    
    # OIDC配置
    oidc_client_id: str = Field(default="", description="OIDC客户端ID", env="OIDC_CLIENT_ID")
    oidc_client_secret: str = Field(default="", description="OIDC客户端秘密", env="OIDC_CLIENT_SECRET")
    oidc_redirect_uri: str = Field(default="", description="OIDC重定向URI", env="OIDC_REDIRECT_URI")
    oidc_issuer: str = Field(default="", description="OIDC发行者", env="OIDC_ISSUER")
    
    # =============================================================================
    # 验证码配置
    # =============================================================================
    verification_code_expire_minutes: int = Field(default=5, description="验证码过期时间(分钟)", env="VERIFICATION_CODE_EXPIRE_MINUTES")
    verification_code_length: int = Field(default=6, description="验证码长度", env="VERIFICATION_CODE_LENGTH")
    
    # =============================================================================
    # 安全配置
    # =============================================================================
    password_min_length: int = Field(default=8, description="密码最小长度", env="PASSWORD_MIN_LENGTH")
    password_require_uppercase: bool = Field(default=True, description="密码是否需要大写字母", env="PASSWORD_REQUIRE_UPPERCASE")
    password_require_lowercase: bool = Field(default=True, description="密码是否需要小写字母", env="PASSWORD_REQUIRE_LOWERCASE")
    password_require_digits: bool = Field(default=True, description="密码是否需要数字", env="PASSWORD_REQUIRE_DIGITS")
    password_require_special_chars: bool = Field(default=True, description="密码是否需要特殊字符", env="PASSWORD_REQUIRE_SPECIAL_CHARS")
    
    # =============================================================================
    # 文件上传配置
    # =============================================================================
    max_file_size_mb: int = Field(default=10, description="最大文件大小(MB)", env="MAX_FILE_SIZE_MB")
    allowed_file_types: list = Field(default=["jpg", "jpeg", "png", "gif", "pdf", "doc", "docx"], description="允许的文件类型", env="ALLOWED_FILE_TYPES")
    
    # =============================================================================
    # 日志配置
    # =============================================================================
    log_level: str = Field(default="INFO", description="日志级别", env="LOG_LEVEL")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="日志格式", env="LOG_FORMAT")
    log_file: str = Field(default="app.log", description="日志文件", env="LOG_FILE")
    log_max_size_mb: int = Field(default=10, description="日志文件最大大小(MB)", env="LOG_MAX_SIZE_MB")
    log_backup_count: int = Field(default=5, description="日志备份文件数量", env="LOG_BACKUP_COUNT")
    
    class Config:
        env_file = "env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def database_url(self) -> str:
        """生成数据库连接URL"""
        if self.database_type.lower() == "postgresql":
            return f"postgresql+asyncpg://{self.postgresql_user}:{self.postgresql_password}@{self.postgresql_host}:{self.postgresql_port}/{self.db_name}"
        elif self.database_type.lower() == "mysql":
            return f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.db_name}"
        else:
            return "sqlite+aiosqlite:///./user_service.db"
    
    @property
    def redis_url(self) -> str:
        """生成Redis连接URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

# 创建全局设置实例
settings = Settings()