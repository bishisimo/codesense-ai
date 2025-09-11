"""
OpenAI模型定义

定义OpenAI提供商的所有AI模型。
"""

from ..models.base import ModelDefinition
from ..models.capabilities import ModelCapabilities, ModelPricing


OPENAI_MODELS = [
        ModelDefinition(
            id="gpt-4",
            provider="openai",
            base_url="https://api.openai.com/v1",
            name="gpt-4",
            display_name="GPT-4",
            model_type="chat",
            version="gpt-4",
            description="GPT-4 模型，强大的多模态AI模型",
            capabilities=ModelCapabilities(
                max_tokens=8192,
                context_window=8192,
                supports_streaming=True,
                supports_function_calling=True,
                supports_code_generation=True,
                supports_code_review=True,
                supports_image_analysis=True,
                response_speed="medium",
                concurrent_requests=5
            ),
            pricing=ModelPricing(
                input_cost_per_1m=30.0,  # 0.03美元/千token = 30美元/百万token
                output_cost_per_1m=60.0,  # 0.06美元/千token = 60美元/百万token
                currency="USD",
                free_tier_limit=0  # 无免费额度
            ),
            is_active=False,
            is_default=False
        ),
        
        ModelDefinition(
            id="gpt-4-turbo",
            provider="openai",
            base_url="https://api.openai.com/v1",
            name="gpt-4-turbo",
            display_name="GPT-4 Turbo",
            model_type="chat",
            version="gpt-4-turbo",
            description="GPT-4 Turbo 模型，更快的响应速度和更大的上下文窗口",
            capabilities=ModelCapabilities(
                max_tokens=128000,
                context_window=128000,
                supports_streaming=True,
                supports_function_calling=True,
                supports_code_generation=True,
                supports_code_review=True,
                supports_image_analysis=True,
                response_speed="fast",
                concurrent_requests=8
            ),
            pricing=ModelPricing(
                input_cost_per_1m=10.0,  # 0.01美元/千token = 10美元/百万token
                output_cost_per_1m=30.0,  # 0.03美元/千token = 30美元/百万token
                currency="USD",
                free_tier_limit=0  # 无免费额度
            ),
            is_active=False,
            is_default=False
        ),
        
        ModelDefinition(
            id="gpt-3.5-turbo",
            provider="openai",
            base_url="https://api.openai.com/v1",
            name="gpt-3.5-turbo",
            display_name="GPT-3.5 Turbo",
            model_type="chat",
            version="gpt-3.5-turbo",
            description="GPT-3.5 Turbo 模型，快速且经济的对话模型",
            capabilities=ModelCapabilities(
                max_tokens=4096,
                context_window=4096,
                supports_streaming=True,
                supports_function_calling=True,
                supports_code_generation=True,
                supports_code_review=True,
                response_speed="fast",
                concurrent_requests=15
            ),
            pricing=ModelPricing(
                input_cost_per_1m=1.0,  # 0.001美元/千token = 1美元/百万token
                output_cost_per_1m=2.0,  # 0.002美元/千token = 2美元/百万token
                currency="USD",
                free_tier_limit=0  # 无免费额度
            ),
            is_active=False,
            is_default=False
        ),
        
        ModelDefinition(
            id="text-embedding-ada-002",
            provider="openai",
            base_url="https://api.openai.com/v1",
            name="text-embedding-ada-002",
            display_name="Text Embedding Ada 002",
            model_type="embedding",
            version="text-embedding-ada-002",
            description="OpenAI 文本嵌入模型，用于文本向量化",
            capabilities=ModelCapabilities(
                max_tokens=8191,
                context_window=8191,
                supports_streaming=False,
                supports_function_calling=False,
                supports_code_generation=False,
                supports_code_review=False,
                supports_embedding=True,
                response_speed="fast",
                concurrent_requests=50
            ),
            pricing=ModelPricing(
                input_cost_per_1m=0.1,  # 0.0001美元/千token = 0.1美元/百万token
                output_cost_per_1m=0.0,  # 嵌入模型只有输入成本
                currency="USD",
                free_tier_limit=0  # 无免费额度
            ),
            is_active=False,
            is_default=False
        )
]
