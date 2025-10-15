from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PermissionBase(BaseModel):
    """权限基础模型"""
    name: str = Field(..., description="权限名称")
    description: Optional[str] = Field(None, description="权限描述")
    resource: str = Field(..., description="资源名称")
    action: str = Field(..., description="操作类型")

class PermissionResponse(PermissionBase):
    """权限响应模型"""
    id: str = Field(..., description="权限ID")
    is_active: bool = Field(True, description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True

class RolePermissionAssign(BaseModel):
    """角色权限分配模型"""
    role_id: str = Field(..., description="角色ID")
    permission_ids: List[str] = Field(..., description="权限ID列表") 