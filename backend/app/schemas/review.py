"""
代码审查相关的Pydantic模式
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class ReviewCommentResponse(BaseModel):
    """审查评论响应模式"""
    id: int = Field(..., description="评论ID")
    review_id: int = Field(..., description="审查ID")
    file_path: Optional[str] = Field(None, description="文件路径")
    line_number: Optional[int] = Field(None, description="行号")
    comment_type: str = Field(..., description="评论类型")
    content: str = Field(..., description="评论内容")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class CodeReviewCreate(BaseModel):
    """创建代码审查请求模式"""
    merge_request_id: int = Field(..., description="合并请求ID")
    commit_sha: str = Field(..., description="提交SHA")
    reviewer_type: str = Field(default="", description="审查者类型")
    
    class Config:
        from_attributes = True


class CodeReviewUpdate(BaseModel):
    """更新代码审查请求模式"""
    score: Optional[int] = Field(None, description="审查得分", ge=0, le=100)
    review_content: Optional[str] = Field(None, description="审查内容")
    status: Optional[str] = Field(None, description="审查状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        from_attributes = True


class CodeReviewBase(BaseModel):
    """代码审查基础模式"""
    merge_request_id: int = Field(..., description="合并请求ID")
    score: Optional[int] = Field(None, description="审查得分", ge=0, le=100)
    review_content: Optional[str] = Field(None, description="审查内容")
    reviewer_type: str = Field(default="", description="审查者类型")
    status: str = Field(default="pending", description="审查状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        from_attributes = True


class CodeReviewResponse(CodeReviewBase):
    """代码审查响应模式"""
    id: int = Field(..., description="审查ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联数据
    comments: List[ReviewCommentResponse] = Field(default=[], description="评论列表")
    
    class Config:
        from_attributes = True


class ReviewResult(BaseModel):
    """审查结果模式"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="结果消息")
    review_id: Optional[int] = Field(None, description="审查ID")
