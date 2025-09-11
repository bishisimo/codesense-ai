"""
DeepSeek模型定义

定义DeepSeek提供商的所有AI模型。
"""

from ..models.base import ModelDefinition
from ..models.capabilities import ModelCapabilities, ModelPricing


DEEPSEEK_MODELS = [
        ModelDefinition(
            id="deepseek-chat",
            provider="deepseek",
            base_url="https://api.deepseek.com/v1",
            name="deepseek-chat",
            display_name="DeepSeek v3.1",
            model_type="chat",
            version="v3.1",
            description="DeepSeek v3.1 模型，专为代码审查和生成优化",
            capabilities=ModelCapabilities(
                max_tokens=8192,
                context_window=8192,
                supports_streaming=True,
                supports_function_calling=True,
                supports_code_generation=True,
                supports_code_review=True,
                response_speed="fast",
                concurrent_requests=10
            ),
            pricing=ModelPricing(
                input_cost_per_1m=4.0,  # 直接调用：4元/百万token
                output_cost_per_1m=12.0,  # 输出：12元/百万token
                cached_input_cost_per_1m=0.5,  # 缓存调用：0.5元/百万token
                currency="CNY",
                free_tier_limit=1000000  # 100万tokens免费额度
            ),
            is_active=True,
            is_default=True
        ),
]
