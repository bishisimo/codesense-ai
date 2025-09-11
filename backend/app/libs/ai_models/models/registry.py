"""
模型注册器

简单的模型注册和查询功能，用于后端模型管理。
"""

from typing import Dict, List, Optional
from .base import ModelDefinition


class ModelRegistry:
    """模型注册器"""
    
    def __init__(self):
        self._models: Dict[str, ModelDefinition] = {}
    
    def register_model(self, definition: ModelDefinition) -> None:
        """注册模型"""
        if not isinstance(definition, ModelDefinition):
            raise TypeError("definition must be a ModelDefinition instance")
        
        if definition.id in self._models:
            raise ValueError(f"Model with id '{definition.id}' already exists")
        
        self._models[definition.id] = definition
    
    def get_model(self, model_id: str) -> Optional[ModelDefinition]:
        """获取模型定义"""
        return self._models.get(model_id)
    
    def list_models(self, active_only: bool = True) -> List[ModelDefinition]:
        """列出所有模型"""
        models = list(self._models.values())
        
        if active_only:
            models = [model for model in models if model.is_active]
        
        # 按提供商和名称排序，DeepSeek优先
        def sort_key(model):
            # DeepSeek模型排在前面
            if model.provider == "deepseek":
                return (0, model.name)
            else:
                return (1, model.provider, model.name)
        
        models.sort(key=sort_key)
        return models
    
    def get_default_model(self) -> Optional[ModelDefinition]:
        """获取默认模型"""
        for model in self._models.values():
            if model.is_default and model.is_active:
                return model
        return None
