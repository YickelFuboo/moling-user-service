import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.models.user import User
from app.infrastructure.redis.factory import REDIS_CONN
from app.constants.common import TOKEN_BLACKLIST_PREFIX


class JWTService:
    """JWT令牌服务类"""
    
    @staticmethod
    def _generate_redis_key(token: str) -> str:
        """生成Redis键"""
        return f"{TOKEN_BLACKLIST_PREFIX}{token}"
    
    @staticmethod
    async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    @staticmethod
    async def create_refresh_token(data: dict):
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    @staticmethod
    async def verify_token(token: str) -> Optional[dict]:
        """验证令牌"""
        try:
            # 首先检查令牌是否在黑名单中
            if await JWTService.is_blacklisted(token):
                logging.warning(f"令牌在黑名单中: {token[:20]}...")
                return None
            
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            username: str = payload.get("sub")
            if username is None:
                return None
            return payload
        except JWTError:
            return None

    @staticmethod
    async def get_current_user(session: AsyncSession, token: str) -> Optional[User]:
        """根据令牌获取当前用户"""
        try:
            payload = await JWTService.verify_token(token)
            if payload is None:
                return None
            
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            return user
        except Exception as e:
            logging.error(f"获取当前用户失败: {e}")
            return None
    
    @staticmethod
    async def add_to_blacklist(token: str, expires_at: Optional[datetime] = None) -> bool:
        """
        将令牌添加到黑名单
        
        Args:
            token: JWT令牌
            expires_at: 令牌过期时间，如果为None则使用默认过期时间
            
        Returns:
            bool: 是否成功添加到黑名单
        """
        try:
            current_time = datetime.utcnow()
            
            if expires_at is None:
                # 使用默认的访问令牌过期时间
                expires_at = current_time + timedelta(minutes=settings.jwt_access_token_expire_minutes)
            
            # 如果令牌已经过期，不添加到黑名单
            if expires_at <= current_time:
                logging.warning(f"令牌已过期，不添加到黑名单: {token[:20]}...")
                return False
            
            # 计算过期时间（秒）
            expire_seconds = int((expires_at - current_time).total_seconds())
            
            # 生成Redis键
            redis_key = JWTService._generate_redis_key(token)
            
            # 存储令牌到Redis，设置过期时间
            success = await REDIS_CONN.set(redis_key, {
                "token": token,
                "added_at": current_time.isoformat(),
                "expires_at": expires_at.isoformat()
            }, expire=expire_seconds)
            
            if success:
                logging.info(f"令牌已添加到Redis黑名单，过期时间: {expires_at}")
                return True
            else:
                logging.error(f"添加令牌到Redis黑名单失败: {token[:20]}...")
                return False
            
        except Exception as e:
            logging.error(f"添加令牌到黑名单失败: {e}")
            return False
    
    @staticmethod
    async def is_blacklisted(token: str) -> bool:
        """
        检查令牌是否在黑名单中
        
        Args:
            token: JWT令牌
            
        Returns:
            bool: 是否在黑名单中
        """
        try:
            redis_key = JWTService._generate_redis_key(token)
            
            # 检查令牌是否存在于Redis中
            blacklist_data = await REDIS_CONN.get(redis_key)
            
            if blacklist_data is not None:
                logging.debug(f"令牌在黑名单中: {token[:20]}...")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"检查令牌黑名单失败: {e}")
            return False
    
    @staticmethod
    async def remove_from_blacklist(token: str) -> bool:
        """
        从黑名单中移除令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            bool: 是否成功移除
        """
        try:
            redis_key = JWTService._generate_redis_key(token)
            
            # 从Redis中删除令牌
            success = await REDIS_CONN.delete(redis_key)
            
            if success:
                logging.info(f"令牌已从Redis黑名单中移除: {token[:20]}...")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"从黑名单移除令牌失败: {e}")
            return False
    
    @staticmethod
    async def get_all_blacklisted_tokens() -> list:
        """
        获取所有黑名单令牌的哈希值列表
        
        Returns:
            list: 黑名单令牌哈希值列表
        """
        try:
            # 获取所有黑名单令牌
            blacklist_keys = await REDIS_CONN.keys("token_blacklist:*")
            blacklisted_tokens = []
            
            for key in blacklist_keys:
                # 从键名中提取令牌（去掉前缀）
                token = key.replace("token_blacklist:", "")
                # 计算令牌哈希值
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                blacklisted_tokens.append(token_hash)
            
            logging.info(f"获取到 {len(blacklisted_tokens)} 个黑名单令牌")
            return blacklisted_tokens
            
        except Exception as e:
            logging.error(f"获取黑名单令牌失败: {e}")
            return [] 