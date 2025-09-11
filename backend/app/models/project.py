"""
项目模型
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Project(Base):
    """项目表"""
    __tablename__ = "project"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    gitlab_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    namespace: Mapped[str] = mapped_column(String(255), nullable=False)
    web_url: Mapped[str] = mapped_column(Text, nullable=False)
    default_branch: Mapped[str] = mapped_column(String(100), default="main")
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
    merge_requests: Mapped[List["MergeRequest"]] = relationship(
        "MergeRequest", 
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', gitlab_id={self.gitlab_id})>"
