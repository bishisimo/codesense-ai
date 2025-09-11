"""
基础模型类

定义AI模型的基本结构和属性。
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from .capabilities import ModelCapabilities, ModelPricing


@dataclass
class ModelDefinition:
    """AI模型定义"""
    
    # 基本信息
    id: str
    provider: str
    base_url: str
    name: str
    display_name: str
    model_type: str = "chat"
    version: Optional[str] = None
    description: Optional[str] = None
    
    # 能力定义
    capabilities: Optional[ModelCapabilities] = None
    
    # 定价信息
    pricing: Optional[ModelPricing] = None
    
    # 状态信息
    is_active: bool = True
    is_default: bool = False
    
    # 元数据
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """初始化后验证"""
        if not self.id:
            raise ValueError("id cannot be empty")
        
        if not self.provider:
            raise ValueError("provider cannot be empty")
        
        if not self.base_url:
            raise ValueError("base_url cannot be empty")
        
        if not self.name:
            raise ValueError("name cannot be empty")
        
        if not self.display_name:
            raise ValueError("display_name cannot be empty")
        
        if not self.model_type:
            raise ValueError("model_type cannot be empty")
    
    def get_full_name(self) -> str:
        """获取完整模型名称"""
        if self.version:
            return f"{self.name} ({self.version})"
        return self.name
    
    
    def supports_feature(self, feature: str) -> bool:
        """检查是否支持指定功能"""
        if not self.capabilities:
            return False
        return self.capabilities.has_capability(feature)
    
    def get_capability_value(self, capability: str) -> Any:
        """获取能力值"""
        if not self.capabilities:
            return None
        return getattr(self.capabilities, capability, None)
    
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "id": self.id,
            "provider": self.provider,
            "base_url": self.base_url,
            "name": self.name,
            "display_name": self.display_name,
            "model_type": self.model_type,
            "version": self.version,
            "description": self.description,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "metadata": self.metadata
        }
        
        if self.capabilities:
            result["capabilities"] = {
                "max_tokens": self.capabilities.max_tokens,
                "context_window": self.capabilities.context_window,
                "supports_streaming": self.capabilities.supports_streaming,
                "supports_function_calling": self.capabilities.supports_function_calling,
                "supports_code_generation": self.capabilities.supports_code_generation,
                "supports_code_review": self.capabilities.supports_code_review,
                "supports_embedding": self.capabilities.supports_embedding,
                "supports_image_analysis": self.capabilities.supports_image_analysis,
                "response_speed": self.capabilities.response_speed,
                "concurrent_requests": self.capabilities.concurrent_requests,
                "custom_capabilities": self.capabilities.custom_capabilities
            }
        
        if self.pricing:
            result["pricing"] = {
                "input_cost_per_1k": self.pricing.input_cost_per_1k,
                "output_cost_per_1k": self.pricing.output_cost_per_1k,
                "currency": self.pricing.currency,
                "monthly_quota": self.pricing.monthly_quota,
                "free_tier_limit": self.pricing.free_tier_limit,
                "enterprise_pricing": self.pricing.enterprise_pricing
            }
        
        return result
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.provider}/{self.display_name}"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"ModelDefinition(id='{self.id}', provider='{self.provider}', name='{self.name}')"
