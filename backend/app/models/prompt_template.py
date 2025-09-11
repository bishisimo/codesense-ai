"""
AI审查Prompt模板模型
"""
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import String, Integer, Text, DateTime, Boolean, JSON, func, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PromptTemplate(Base):
    """AI审查Prompt模板表"""
    __tablename__ = "prompt_template"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template_content: Mapped[str] = mapped_column(Text, nullable=False)
    variables_schema: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)  # 变量定义
    # output_format 字段已移除，由后端统一管理
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)  # 默认不激活，需要验证通过
    generation_status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending, success, failed
    validation_errors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 验证失败的错误信息
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, index=True)  # 是否由AI生成
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
    created_by: Mapped[str] = mapped_column(String(50), nullable=False)
    template_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)  # system/manual/ai_generated
    
    # 索引
    __table_args__ = (
        Index('idx_prompt_templates_default', 'is_default'),
        Index('idx_prompt_templates_active', 'is_active'),
        Index('idx_prompt_templates_created_by', 'created_by'),
        Index('idx_prompt_templates_generation_status', 'generation_status'),
        Index('idx_prompt_templates_ai_generated', 'ai_generated'),
        Index('idx_prompt_templates_source', 'template_source'),
    )
