"""
模型能力定义

定义AI模型的技术能力、性能指标和定价信息。
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ModelCapabilities:
    """模型能力定义"""
    
    # 基础能力
    max_tokens: int
    context_window: int = 4096
    supports_streaming: bool = False
    supports_function_calling: bool = False
    
    # 功能能力
    supports_code_generation: bool = False
    supports_code_review: bool = False
    supports_embedding: bool = False
    supports_image_analysis: bool = False
    
    # 性能能力
    response_speed: Optional[str] = None  # fast, medium, slow
    concurrent_requests: Optional[int] = None
    
    # 自定义能力字段
    custom_capabilities: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """初始化后验证"""
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        
        if self.context_window <= 0:
            raise ValueError("context_window must be positive")
        
        if self.context_window > self.max_tokens:
            raise ValueError("context_window cannot exceed max_tokens")
        
        if self.concurrent_requests is not None and self.concurrent_requests <= 0:
            raise ValueError("concurrent_requests must be positive")
    
    def has_capability(self, capability: str) -> bool:
        """检查是否具有指定能力"""
        return getattr(self, capability, False)


@dataclass
class ModelPricing:
    """模型定价信息"""
    
    # 基础定价（元/百万token）
    input_cost_per_1m: float  # 每百万输入token成本（直接调用）
    output_cost_per_1m: float  # 每百万输出token成本
    currency: str = "CNY"  # 默认使用人民币
    
    # 缓存定价（元/百万token）
    cached_input_cost_per_1m: Optional[float] = None  # 每百万缓存输入token成本
    cached_output_cost_per_1m: Optional[float] = None  # 每百万缓存输出token成本
    
    # 可选定价信息
    monthly_quota: Optional[int] = None  # 月度配额
    free_tier_limit: Optional[int] = None  # 免费额度
    enterprise_pricing: Optional[Dict[str, Any]] = None  # 企业定价
    
    def __post_init__(self):
        """初始化后验证"""
        if self.input_cost_per_1m < 0:
            raise ValueError("input_cost_per_1m cannot be negative")
        
        if self.output_cost_per_1m < 0:
            raise ValueError("output_cost_per_1m cannot be negative")
        
        if not self.currency:
            raise ValueError("currency cannot be empty")
        
        if self.monthly_quota is not None and self.monthly_quota <= 0:
            raise ValueError("monthly_quota must be positive")
        
        if self.free_tier_limit is not None and self.free_tier_limit < 0:
            raise ValueError("free_tier_limit cannot be negative")
    
    def calculate_cost(self, input_tokens: int, output_tokens: int, 
                      direct_tokens: int = 0, cache_tokens: int = 0) -> float:
        """计算使用成本
        
        Args:
            input_tokens: 总输入token数
            output_tokens: 输出token数
            direct_tokens: 直接调用token数
            cache_tokens: 缓存token数
        """
        # 如果没有提供直接和缓存token数，使用传统计算方式
        if direct_tokens == 0 and cache_tokens == 0:
            input_cost = (input_tokens / 1000000) * self.input_cost_per_1m
            output_cost = (output_tokens / 1000000) * self.output_cost_per_1m
            return input_cost + output_cost
        
        # 使用新的定价结构（元/百万token）
        # 直接调用成本
        direct_input_cost = (direct_tokens / 1000000) * self.input_cost_per_1m
        
        # 缓存调用成本
        cache_input_cost = 0
        if self.cached_input_cost_per_1m is not None:
            cache_input_cost = (cache_tokens / 1000000) * self.cached_input_cost_per_1m
        else:
            # 如果没有缓存定价，使用直接调用定价
            cache_input_cost = (cache_tokens / 1000000) * self.input_cost_per_1m
        
        # 输出成本（通常缓存和直接调用相同）
        output_cost = (output_tokens / 1000000) * self.output_cost_per_1m
        
        return direct_input_cost + cache_input_cost + output_cost
    
    def is_within_free_tier(self, total_tokens: int) -> bool:
        """检查是否在免费额度内"""
        if self.free_tier_limit is None:
            return False
        return total_tokens <= self.free_tier_limit
