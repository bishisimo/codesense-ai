"""
AI模型定义模块

提供统一的AI模型定义标准，支持简单的模型扩展机制。
专注于模型定义，不涉及业务逻辑和数据库操作。
"""

from .models.base import ModelDefinition
from .models.capabilities import ModelCapabilities, ModelPricing
from .models.registry import ModelRegistry
from .utils.validation import validate_model_definition

# 全局模型注册器实例
_registry = ModelRegistry()

def get_model_definition(model_id: str) -> ModelDefinition:
    """获取模型定义"""
    return _registry.get_model(model_id)

def list_models(active_only: bool = True) -> list[ModelDefinition]:
    """列出所有模型"""
    return _registry.list_models(active_only=active_only)

def register_model(definition: ModelDefinition) -> None:
    """注册新模型"""
    _registry.register_model(definition)

def validate_definition(definition: ModelDefinition) -> bool:
    """验证模型定义"""
    return validate_model_definition(definition)



# 初始化默认模型
def _init_default_models():
    """初始化默认模型定义"""
    from .providers.deepseek import DEEPSEEK_MODELS
    from .providers.openai import OPENAI_MODELS
    from .providers.claude import CLAUDE_MODELS
    
    # 注册模型
    for model in DEEPSEEK_MODELS:
        _registry.register_model(model)

# 模块初始化时自动注册默认模型
_init_default_models()

__all__ = [
    "ModelDefinition",
    "ModelCapabilities", 
    "ModelPricing",
    "get_model_definition",
    "list_models",
    "register_model",
    "validate_definition"
]
