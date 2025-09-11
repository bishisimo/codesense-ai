"""
AI模型和Token使用相关的Pydantic模式
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AIModelBase(BaseModel):
    """AI模型基础模式"""
    provider: str = Field(..., description="厂商名称")
    model_name: str = Field(..., description="模型名称")
    display_name: str = Field(..., description="显示名称")
    model_type: str = Field(..., description="模型类型")
    version: Optional[str] = Field(None, description="版本号")
    description: Optional[str] = Field(None, description="模型描述")
    capabilities: Optional[Dict[str, Any]] = Field(None, description="能力配置")
    pricing: Optional[Dict[str, Any]] = Field(None, description="定价信息")
    is_active: bool = Field(True, description="是否启用")
    is_default: bool = Field(False, description="是否为默认模型")


class AIModelCreate(AIModelBase):
    """创建AI模型"""
    pass


class AIModelUpdate(BaseModel):
    """更新AI模型"""
    display_name: Optional[str] = Field(None, description="显示名称")
    description: Optional[str] = Field(None, description="模型描述")
    capabilities: Optional[Dict[str, Any]] = Field(None, description="能力配置")
    pricing: Optional[Dict[str, Any]] = Field(None, description="定价信息")
    is_active: Optional[bool] = Field(None, description="是否启用")
    is_default: Optional[bool] = Field(None, description="是否为默认模型")


class AIModelResponse(AIModelBase):
    """AI模型响应"""
    id: int = Field(..., description="模型ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class TokenUsageBase(BaseModel):
    """Token使用基础模式"""
    model_id: int = Field(..., description="模型ID")
    review_id: Optional[int] = Field(None, description="审查ID")
    usage_type: str = Field(..., description="使用类型")
    total_tokens: int = Field(0, description="总token数")
    prompt_tokens: int = Field(0, description="输入token数")
    completion_tokens: int = Field(0, description="输出token数")
    direct_tokens: int = Field(0, description="直接调用token数")
    cache_tokens: int = Field(0, description="缓存token数")
    cost: Optional[float] = Field(None, description="成本（人民币）")
    request_duration: Optional[float] = Field(None, description="请求耗时")
    created_at: datetime = Field(..., description="创建时间")


class TokenUsageRequest(TokenUsageBase):
    """Token使用请求"""
    pass


class TokenUsageResponse(TokenUsageBase):
    """Token使用响应"""
    id: int = Field(..., description="使用记录ID")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class ModelStats(BaseModel):
    """模型统计信息"""
    provider: str = Field(..., description="厂商")
    model_name: str = Field(..., description="模型名称")
    requests: int = Field(..., description="请求次数")
    tokens: int = Field(..., description="token总数")
    cost: float = Field(..., description="总成本（人民币）")


class TypeStats(BaseModel):
    """使用类型统计信息"""
    usage_type: str = Field(..., description="使用类型")
    requests: int = Field(..., description="请求次数")
    tokens: int = Field(..., description="token总数")
    cost: float = Field(..., description="总成本（人民币）")


class TokenUsageStats(BaseModel):
    """Token使用统计"""
    period: str = Field(..., description="统计周期")
    start_date: datetime = Field(..., description="开始时间")
    end_date: datetime = Field(..., description="结束时间")
    total_requests: int = Field(..., description="总请求数")
    total_tokens: int = Field(..., description="总token数")
    total_prompt_tokens: int = Field(..., description="总输入token数")
    total_completion_tokens: int = Field(..., description="总输出token数")
    total_direct_tokens: int = Field(..., description="总直接token数")
    total_cache_tokens: int = Field(..., description="总缓存token数")
    total_cost: float = Field(..., description="总成本（人民币）")
    model_stats: List[ModelStats] = Field(..., description="按模型统计")
    type_stats: List[TypeStats] = Field(..., description="按类型统计")
