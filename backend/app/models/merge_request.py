"""
合并请求模型
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MergeRequest(Base):
    """合并请求表"""
    __tablename__ = "merge_request"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    gitlab_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("project.id"), 
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_branch: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_branch: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # opened, closed, merged
    mr_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # MR在GitLab中的创建时间
    mr_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # MR在GitLab中的更新时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)  # 数据库记录创建时间
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)  # 数据库记录更新时间
    commits_count: Mapped[int] = mapped_column(Integer, default=0)
    changes_count: Mapped[int] = mapped_column(Integer, default=0)
    additions_count: Mapped[int] = mapped_column(Integer, default=0)  # 新增行数
    deletions_count: Mapped[int] = mapped_column(Integer, default=0)  # 删除行数
    last_commit_sha: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)  # 最新commit SHA
    
    # 关系
    project: Mapped["Project"] = relationship("Project", back_populates="merge_requests")
    code_reviews: Mapped[List["CodeReview"]] = relationship(
        "CodeReview", 
        back_populates="merge_request",
        cascade="all, delete-orphan"
    )
    
    # 索引和约束
    __table_args__ = (
        # 项目内GitLab ID唯一约束
        UniqueConstraint("project_id", "gitlab_id", name="uq_mr_project_gitlab_id"),
        # 索引
        Index("idx_mr_project_state", "project_id", "state"),
        Index("idx_mr_created_at", "created_at"),
        Index("idx_mr_updated_at", "updated_at"),

    )
    
    def __repr__(self) -> str:
        return f"<MergeRequest(id={self.id}, gitlab_id={self.gitlab_id}, title='{self.title[:50]}...')>"
