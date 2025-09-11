"""
项目相关的Pydantic模式
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """项目基础模式"""
    name: str = Field(..., description="项目名称")
    namespace: str = Field(..., description="项目命名空间")
    web_url: str = Field(..., description="项目Web URL")
    default_branch: str = Field(default="main", description="默认分支")


class ProjectCreate(ProjectBase):
    """创建项目模式"""
    gitlab_id: int = Field(..., description="GitLab项目ID")


class ProjectUpdate(BaseModel):
    """更新项目模式"""
    name: Optional[str] = Field(None, description="项目名称")
    namespace: Optional[str] = Field(None, description="项目命名空间")
    web_url: Optional[str] = Field(None, description="项目Web URL")
    default_branch: Optional[str] = Field(None, description="默认分支")


class ProjectResponse(ProjectBase):
    """项目响应模式"""
    id: int = Field(..., description="项目ID")
    gitlab_id: int = Field(..., description="GitLab项目ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True
