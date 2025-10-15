from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field


T = TypeVar('T')


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(default=True, description="请求是否成功")
    message: Optional[str] = Field(default=None, description="响应消息")
    data: Optional[Any] = Field(default=None, description="响应数据")


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    success: bool = Field(default=False, description="请求失败")
    error_code: Optional[str] = Field(default=None, description="错误代码")
    error_details: Optional[dict] = Field(default=None, description="错误详情")


class PaginationParams(BaseModel):
    """分页参数模型"""
    page: int = Field(default=1, ge=1, description="页码，从1开始")
    page_size: int = Field(default=10, ge=1, le=100, description="每页大小，最大100")
    keyword: Optional[str] = Field(default=None, max_length=50, description="搜索关键词")
    search_fields: Optional[str] = Field(default=None, description="搜索字段，多个字段用逗号分隔，如：name,email,phone,role")


class PaginatedResponse(BaseResponse, Generic[T]):
    """分页响应模型"""
    data: List[T] = Field(description="数据列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    size: int = Field(description="每页大小")
    pages: int = Field(description="总页数")
    
    @classmethod
    def create(cls, data: List[T], total: int, page: int, size: int) -> "PaginatedResponse[T]":
        """创建分页响应"""
        pages = (total + size - 1) // size  # 计算总页数
        return cls(
            data=data,
            total=total,
            page=page,
            size=size,
            pages=pages
        ) 