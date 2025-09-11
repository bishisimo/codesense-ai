"""
Claude模型定义

定义Anthropic Claude提供商的所有AI模型。
"""

from ..models.base import ModelDefinition
from ..models.capabilities import ModelCapabilities, ModelPricing


CLAUDE_MODELS = [
        ModelDefinition(
            id="claude-3-opus",
            provider="claude",
            base_url="https://api.anthropic.com/v1",
            name="claude-3-opus",
            display_name="Claude 3 Opus",
            model_type="chat",
            version="claude-3-opus-20240229",
            description="Claude 3 Opus 模型，最强大的Claude模型，擅长复杂推理任务",
            capabilities=ModelCapabilities(
                max_tokens=200000,
                context_window=200000,
                supports_streaming=True,
                supports_function_calling=False,
                supports_code_generation=True,
                supports_code_review=True,
                supports_image_analysis=True,
                response_speed="medium",
                concurrent_requests=3
            ),
            pricing=ModelPricing(
                input_cost_per_1m=15.0,  # 0.015美元/千token = 15美元/百万token
                output_cost_per_1m=75.0,  # 0.075美元/千token = 75美元/百万token
                currency="USD",
                free_tier_limit=0  # 无免费额度
            ),
            is_active=False,
            is_default=False
        ),
        
        ModelDefinition(
            id="claude-3-sonnet",
            provider="claude",
            base_url="https://api.anthropic.com/v1",
            name="claude-3-sonnet",
            display_name="Claude 3 Sonnet",
            model_type="chat",
            version="claude-3-sonnet-20240229",
            description="Claude 3 Sonnet 模型，平衡性能和速度的模型",
            capabilities=ModelCapabilities(
                max_tokens=200000,
                context_window=200000,
                supports_streaming=True,
                supports_function_calling=False,
                supports_code_generation=True,
                supports_code_review=True,
                supports_image_analysis=True,
                response_speed="fast",
                concurrent_requests=5
            ),
            pricing=ModelPricing(
                input_cost_per_1m=3.0,  # 0.003美元/千token = 3美元/百万token
                output_cost_per_1m=15.0,  # 0.015美元/千token = 15美元/百万token
                currency="USD",
                free_tier_limit=0  # 无免费额度
            ),
            is_active=False,
            is_default=False
        ),
        
        ModelDefinition(
            id="claude-3-haiku",
            provider="claude",
            base_url="https://api.anthropic.com/v1",
            name="claude-3-haiku",
            display_name="Claude 3 Haiku",
            model_type="chat",
            version="claude-3-haiku-20240307",
            description="Claude 3 Haiku 模型，快速且经济的模型",
            capabilities=ModelCapabilities(
                max_tokens=200000,
                context_window=200000,
                supports_streaming=True,
                supports_function_calling=False,
                supports_code_generation=True,
                supports_code_review=True,
                supports_image_analysis=True,
                response_speed="fast",
                concurrent_requests=10
            ),
            pricing=ModelPricing(
                input_cost_per_1m=0.25,  # 0.00025美元/千token = 0.25美元/百万token
                output_cost_per_1m=1.25,  # 0.00125美元/千token = 1.25美元/百万token
                currency="USD",
                free_tier_limit=0  # 无免费额度
            ),
            is_active=False,
            is_default=False
        ),
        
        ModelDefinition(
            id="claude-2.1",
            provider="claude",
            base_url="https://api.anthropic.com/v1",
            name="claude-2.1",
            display_name="Claude 2.1",
            model_type="chat",
            version="claude-2.1",
            description="Claude 2.1 模型，稳定可靠的对话模型",
            capabilities=ModelCapabilities(
                max_tokens=100000,
                context_window=100000,
                supports_streaming=True,
                supports_function_calling=False,
                supports_code_generation=True,
                supports_code_review=True,
                response_speed="medium",
                concurrent_requests=8
            ),
            pricing=ModelPricing(
                input_cost_per_1m=8.0,  # 0.008美元/千token = 8美元/百万token
                output_cost_per_1m=24.0,  # 0.024美元/千token = 24美元/百万token
                currency="USD",
                free_tier_limit=0  # 无免费额度
            ),
            is_active=False,
            is_default=False
        )
]
