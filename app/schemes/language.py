from pydantic import BaseModel, Field

class ChangeLanguageRequest(BaseModel):
    """切换语言请求模型"""
    language: str = Field(..., description="目标语言代码", pattern="^(zh-CN|en-US)$") 