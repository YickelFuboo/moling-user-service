import base64
import hashlib
import json
import logging
from fastapi import APIRouter, HTTPException, status
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from app.config import settings
from app.schemes.common import BaseResponse
from app.services.auth_mgmt.jwt_service import JWTService
from app.infrastructure.redis.factory import REDIS_CONN


router = APIRouter()


@router.get("/.well-known/jwks.json")
async def get_jwks():
    """
    获取JWKS (JSON Web Key Set) - 供其他微服务获取公钥
    
    这是标准的JWKS端点，其他微服务可以通过此接口获取公钥进行JWT本地验证
    """
    try:
        # 从配置中获取公钥
        # 注意：在生产环境中，应该使用非对称加密（如RSA）
        # 这里为了简化，使用对称加密的密钥作为示例
        
        # 生成JWKS格式的公钥信息
        jwks = {
            "keys": [
                {
                    "kty": "oct",  # 对称密钥类型
                    "k": base64.urlsafe_b64encode(
                        settings.jwt_secret_key.encode('utf-8')
                    ).decode('utf-8').rstrip('='),
                    "alg": settings.jwt_algorithm,
                    "use": "sig",
                    "kid": "user-service-key-1"
                }
            ]
        }
        
        return jwks
        
    except Exception as e:
        logging.error(f"获取JWKS失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取JWKS失败"
        )


@router.get("/jwt-config")
async def get_jwt_config():
    """
    获取JWT配置信息 - 供其他微服务获取JWT验证所需的配置
    
    返回JWT算法、密钥ID等信息，方便其他微服务进行本地验证
    """
    try:
        config = {
            "algorithm": settings.jwt_algorithm,
            "issuer": settings.app_name,  # 发行者
            "audience": "microservices",  # 受众
            "key_id": "user-service-key-1",
            "jwks_url": "/api/v1/jwt/.well-known/jwks.json",
            "token_expire_minutes": settings.jwt_access_token_expire_minutes,
            "refresh_token_expire_days": settings.jwt_refresh_token_expire_days
        }
        
        return BaseResponse(
            success=True,
            message="获取JWT配置成功",
            data=config
        )
        
    except Exception as e:
        logging.error(f"获取JWT配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取JWT配置失败"
        )

@router.get("/blacklist")
async def get_blacklist():
    """
    获取JWT黑名单 - 供其他微服务获取黑名单信息
    
    注意：为了安全，只返回令牌的哈希值，不返回完整令牌
    """
    try:
        blacklisted_tokens = await JWTService.get_all_blacklisted_tokens()
        
        return BaseResponse(
            success=True,
            message="获取黑名单成功",
            data={
                "blacklisted_tokens": blacklisted_tokens,
                "count": len(blacklisted_tokens)
            }
        )
        
    except Exception as e:
        logging.error(f"获取黑名单失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取黑名单失败"
        )
