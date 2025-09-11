"""
代码审查模型
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, func, CheckConstraint, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CodeReview(Base):
    """代码审查表"""
    __tablename__ = "code_review"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    merge_request_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("merge_request.id"), 
        nullable=False,
        index=True
    )
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 详细评分
    review_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Markdown格式
    code_suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 代码修改建议
    reviewer_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 记录实际使用的模型名称
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 错误信息
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # 关系
    merge_request: Mapped["MergeRequest"] = relationship("MergeRequest", back_populates="code_reviews")
    comments: Mapped[List["ReviewComment"]] = relationship(
        "ReviewComment", 
        back_populates="review",
        cascade="all, delete-orphan"
    )
    token_usages: Mapped[List["TokenUsage"]] = relationship(
        "TokenUsage", 
        back_populates="code_review",
        cascade="all, delete-orphan"
    )
    
    # 约束
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="score_range_check"),
        Index("idx_review_mr_commit", "merge_request_id", "commit_sha"),
        Index("idx_review_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<CodeReview(id={self.id}, mr_id={self.merge_request_id}, score={self.score})>"


class ReviewComment(Base):
    """审查评论表"""
    __tablename__ = "review_comment"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    review_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("code_review.id"), 
        nullable=False,
        index=True
    )
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    line_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comment_type: Mapped[str] = mapped_column(String(50), nullable=False)  # suggestion, warning, error, info
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    # 关系
    review: Mapped["CodeReview"] = relationship("CodeReview", back_populates="comments")
    
    # 索引
    __table_args__ = (
        Index("idx_comment_review", "review_id"),
        Index("idx_comment_type", "comment_type"),
        Index("idx_comment_file", "file_path"),
    )
    
    def __repr__(self) -> str:
        return f"<ReviewComment(id={self.id}, review_id={self.review_id}, type={self.comment_type})>"
