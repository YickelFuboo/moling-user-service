import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入我们的模型
from app.models.base import Base
from app.config.settings import settings

# 导入所有模型以确保它们被注册到Base.metadata中
from app.models.user import User, FileMetadata
from app.models.role import Role, UserInRole
from app.models.permission import Permission, RolePermission
from app.models.tenant import Tenant

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 设置数据库URL - alembic需要使用同步驱动
import urllib.parse

if settings.database_type.lower() == "postgresql":
    # 对密码进行URL编码以处理特殊字符
    encoded_password = urllib.parse.quote_plus(settings.postgresql_password)
    database_url = f"postgresql+psycopg2://{settings.postgresql_user}:{encoded_password}@{settings.postgresql_host}:{settings.postgresql_port}/{settings.db_name}"
    print(f"使用PostgreSQL数据库: {settings.postgresql_host}:{settings.postgresql_port}/{settings.db_name}")
elif settings.database_type.lower() == "mysql":
    # 对密码进行URL编码以处理特殊字符
    encoded_password = urllib.parse.quote_plus(settings.mysql_password)
    database_url = f"mysql+pymysql://{settings.mysql_user}:{encoded_password}@{settings.mysql_host}:{settings.mysql_port}/{settings.db_name}"
    print(f"使用MySQL数据库: {settings.mysql_host}:{settings.mysql_port}/{settings.db_name}")
else:
    database_url = "sqlite:///./user_service.db"
    print("使用SQLite数据库")

config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
