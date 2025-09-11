"""
AI模型信息表
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Integer, Text, DateTime, Boolean, JSON, func, Index, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AIModel(Base):
    """AI模型信息表"""
    __tablename__ = "ai_model"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 厂商：openai, anthropic, google, etc.
    base_url: Mapped[str] = mapped_column(String(200), nullable=False)  # API基础URL
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # 模型名称：gpt-4, claude-3, etc.
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)  # 显示名称：GPT-4, Claude-3 Sonnet, etc.
    model_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # 模型类型：chat, completion, embedding, etc.
    version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 版本号
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 模型描述
    capabilities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 能力配置：{"max_tokens": 4096, "supports_streaming": true}
    pricing: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 定价信息：{"input": 0.03, "output": 0.06}
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)  # 是否启用
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)  # 是否为默认模型
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
    token_usages: Mapped[List["TokenUsage"]] = relationship(
        "TokenUsage", 
        back_populates="ai_model",
        cascade="all, delete-orphan"
    )
    
    # 索引和约束
    __table_args__ = (
        Index("idx_model_provider_name", "provider", "model_name"),
        Index("idx_model_active", "is_active", "model_type"),
        UniqueConstraint("model_name", name="uq_ai_models_model_name"),  # 模型名称全局唯一
    )
    
    def __repr__(self) -> str:
        return f"<AIModel(id={self.id}, provider='{self.provider}', model_name='{self.model_name}')>"


class TokenUsage(Base):
    """Token使用记录表"""
    __tablename__ = "token_usage"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("ai_model.id"), 
        nullable=False,
        index=True
    )
    review_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("code_review.id"), 
        nullable=True,
        index=True
    )
    usage_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # 使用类型：review, generation, etc.
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 总token数
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 输入token数
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 输出token数
    direct_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 直接调用token数
    cache_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 缓存token数
    cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 成本（人民币）
    request_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 请求耗时（秒）
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # 关系
    ai_model: Mapped["AIModel"] = relationship("AIModel", back_populates="token_usages")
    code_review: Mapped[Optional["CodeReview"]] = relationship("CodeReview", back_populates="token_usages")
    
    # 索引
    __table_args__ = (
        Index("idx_token_usage_model_date", "model_id", "created_at"),
        Index("idx_token_usage_type_date", "usage_type", "created_at"),
        Index("idx_token_usage_review", "review_id"),
    )
    
    def __repr__(self) -> str:
        return f"<TokenUsage(id={self.id}, model_id={self.model_id}, total_tokens={self.total_tokens})>"
