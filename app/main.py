"""
User-Service 主入口文件
"""
import uvicorn
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.logger import set_log_level, setup_logging
from app.middleware.logging import logging_middleware
from app.config.settings import settings, APP_NAME, APP_VERSION, APP_DESCRIPTION
from app.infrastructure.database import close_db, health_check_db
from app.infrastructure.storage import STORAGE_CONN
from app.infrastructure.redis import REDIS_CONN
from app.api.v1 import users, auth, roles, oauth, permissions, language, jwt_keys


#==================================
# 创建FastAPI应用
#==================================
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
)

#==================================
# 配置打印日志
#==================================
setup_logging()

#==================================
# 配置中间件
#==================================
# 配置CORS中间件 - 直接使用FastAPI内置的CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置日志中间件 - 直接使用全局中间件实例
app.add_middleware(logging_middleware)

#==================================
# 注册所有路由器
#==================================
app.include_router(users.router, prefix="/api/v1/users", tags=["用户管理"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证管理"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["角色管理"])
app.include_router(permissions.router, prefix="/api/v1/permissions", tags=["权限管理"])
app.include_router(oauth.router, prefix="/api/v1/oauth", tags=["第三方登录"])
app.include_router(jwt_keys.router, prefix="/api/v1/jwt", tags=["JWT密钥服务"])
app.include_router(language.router, prefix="/api/v1/language", tags=["语言管理"])

#==================================
# 初始化基础设施
#==================================
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    try:      
        logging.info("开始应用启动流程...")
        
        logging.info(f"{APP_NAME} v{APP_VERSION} 启动成功")

    except Exception as e:
        logging.error(f"应用启动失败: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    try:
        # 关闭数据库连接
        await close_db()
        
        # 关闭存储连接
        if STORAGE_CONN and hasattr(STORAGE_CONN, 'close'):
            try:
                await STORAGE_CONN.close()
            except Exception as e:
                logging.warning(f"关闭存储连接时出错: {e}")
        logging.info("存储连接已关闭")

        # 关闭Redis连接
        if REDIS_CONN and hasattr(REDIS_CONN, 'close'):
            try:
                await REDIS_CONN.close()
            except Exception as e:
                logging.warning(f"关闭Redis连接时出错: {e}")
        logging.info("Redis连接已关闭")
        
    except Exception as e:
        logging.error(f"关闭连接失败: {e}")
    
    logging.info("应用正在关闭...")

# 根路径
@app.get("/")
async def root():
    """根路径 - 服务信息"""
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "docs": "/docs",
        "health": "/health",
        "api_base": "/api/v1"
    }


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        # 基础服务状态检查
        health_status = {
            "status": "healthy",
            "service": APP_NAME,
            "version": APP_VERSION,
            "timestamp": datetime.now().isoformat(),
            "environment": "development" if settings.debug else "production"
        }
    
        # 检查数据库连接健康状态
        db_healthy = await health_check_db()
        health_status["database"] = "healthy" if db_healthy else "unhealthy"

        # 检查存储连接健康状态
        storage_healthy = False
        if STORAGE_CONN and hasattr(STORAGE_CONN, 'health_check'):
            storage_healthy = await STORAGE_CONN.health_check()
        health_status["storage"] = "healthy" if storage_healthy else "unhealthy"
        
        # 检查Redis连接健康状态
        redis_healthy = False
        if REDIS_CONN and hasattr(REDIS_CONN, 'health_check'):
            redis_healthy = await REDIS_CONN.health_check()
        health_status["redis"] = "healthy" if redis_healthy else "unhealthy"
        
        # 如果任何服务不健康，整体状态设为不健康
        if not db_healthy or not storage_healthy or  not redis_healthy:
            health_status["status"] = "unhealthy"
                
        return health_status
        
    except Exception as e:
        logging.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail="服务不健康")

@app.post("/log-level")
async def change_log_level(level: str = Query(..., description="日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL")):
    """动态设置日志级别"""
    try:
        set_log_level(level)
        current_level = logging.getLevelName(logging.getLogger().getEffectiveLevel())
        return {
            "message": f"日志级别已设置为 {level.upper()}",
            "current_level": current_level
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/log-level")
async def get_log_level():
    """获取当前日志级别"""
    current_level = logging.getLevelName(logging.getLogger().getEffectiveLevel())
    return {
        "current_level": current_level
    }

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logging.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "内部服务器错误"}
    )

def main():
    """主函数，用于启动服务器"""
    uvicorn.run(
        "app.main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=settings.debug
    )

if __name__ == "__main__":
    main() 