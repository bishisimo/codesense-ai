"""
合并请求相关的Pydantic模式
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from .review import CodeReviewResponse


class MergeRequestBase(BaseModel):
    """合并请求基础模式"""
    title: str = Field(..., description="合并请求标题")
    description: Optional[str] = Field(None, description="合并请求描述")
    author: str = Field(..., description="作者")
    source_branch: str = Field(..., description="源分支")
    target_branch: str = Field(..., description="目标分支")
    state: str = Field(..., description="状态")


class MergeRequestCreate(MergeRequestBase):
    """创建合并请求模式"""
    gitlab_id: int = Field(..., description="GitLab合并请求ID")
    project_id: int = Field(..., description="项目ID")
    mr_created_at: datetime = Field(..., description="MR在GitLab中的创建时间")
    mr_updated_at: datetime = Field(..., description="MR在GitLab中的更新时间")
    commits_count: int = Field(default=0, description="提交数量")
    changes_count: int = Field(default=0, description="更改行数")


class MergeRequestUpdate(BaseModel):
    """更新合并请求模式"""
    title: Optional[str] = Field(None, description="合并请求标题")
    description: Optional[str] = Field(None, description="合并请求描述")
    state: Optional[str] = Field(None, description="状态")
    mr_updated_at: Optional[datetime] = Field(None, description="MR在GitLab中的更新时间")
    commits_count: Optional[int] = Field(None, description="提交数量")
    changes_count: Optional[int] = Field(None, description="更改行数")


class MergeRequestResponse(MergeRequestBase):
    """合并请求响应模式"""
    id: int = Field(..., description="合并请求ID")
    gitlab_id: int = Field(..., description="GitLab合并请求ID")
    project_id: int = Field(..., description="项目ID")
    mr_created_at: datetime = Field(..., description="MR在GitLab中的创建时间")
    mr_updated_at: datetime = Field(..., description="MR在GitLab中的更新时间")
    created_at: datetime = Field(..., description="数据库记录创建时间")
    updated_at: datetime = Field(..., description="数据库记录更新时间")
    commits_count: int = Field(..., description="提交数量")
    changes_count: int = Field(..., description="更改行数")
    additions_count: int = Field(..., description="新增行数")
    deletions_count: int = Field(..., description="删除行数")
    
    # 关联数据
    latest_review: Optional[CodeReviewResponse] = Field(None, description="最新审查")
    review_status: str = Field(default="未审查", description="审查状态")
    
    class Config:
        from_attributes = True


class MergeRequestListItem(BaseModel):
    """合并请求列表项模式"""
    id: int = Field(..., description="合并请求ID")
    gitlab_id: int = Field(..., description="GitLab合并请求ID")
    title: str = Field(..., description="标题")
    author: str = Field(..., description="作者")
    source_branch: str = Field(..., description="源分支")
    target_branch: str = Field(..., description="目标分支")
    state: str = Field(..., description="状态")
    mr_created_at: datetime = Field(..., description="MR在GitLab中的创建时间")
    mr_updated_at: datetime = Field(..., description="MR在GitLab中的更新时间")
    commits_count: int = Field(..., description="提交数量")
    changes_count: int = Field(..., description="更改行数")
    additions_count: int = Field(..., description="新增行数")
    deletions_count: int = Field(..., description="删除行数")
    
    # 项目信息
    project_name: str = Field(..., description="项目名称")
    project_web_url: str = Field(..., description="项目GitLab URL")
    
    # 审查信息
    review_status: str = Field(default="未审查", description="审查状态")
    review_score: Optional[int] = Field(None, description="审查得分")
    review_id: Optional[int] = Field(None, description="审查ID")
    is_reviewed: Optional[int] = Field(None, description="是否已审查：0=未审查，1=已审查")
    is_latest_reviewed: Optional[int] = Field(None, description="是否最新提交已审查：0=未审查，1=已审查")
    is_reviewing: Optional[int] = Field(None, description="是否正在审查中：0=非审查中，1=审查中")
    is_failed: Optional[int] = Field(None, description="是否审查失败：0=非失败，1=失败")
    last_commit_sha: Optional[str] = Field(None, description="最新commit SHA")
    commit_id: Optional[str] = Field(None, description="简短的commit ID（前8位）")
    
    class Config:
        from_attributes = True


class MergeRequestListResponse(BaseModel):
    """合并请求列表响应模式"""
    items: List[MergeRequestListItem] = Field(..., description="列表项")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="页大小")
    pages: int = Field(..., description="总页数")
