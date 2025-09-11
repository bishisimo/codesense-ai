"""
AI服务模块

提供统一的AI服务层，包括：
- AIService: 统一的AI模型调用服务
- 各种AI业务服务（模板生成、提示词优化等）
"""
from .ai_service import AIService, ai_service
from .template_generator import TemplateGeneratorService
from .prompt_optimizer import PromptOptimizerService

# 创建服务实例
template_generator = TemplateGeneratorService(ai_service)
prompt_optimizer = PromptOptimizerService(ai_service)

__all__ = [
    "AIService",
    "ai_service",
    "TemplateGeneratorService",
    "template_generator",
    "PromptOptimizerService",
    "prompt_optimizer"
]
