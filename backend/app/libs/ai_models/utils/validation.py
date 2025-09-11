"""
模型定义验证工具

提供模型定义、能力、定价等验证功能。
"""

import re
from typing import List, Dict, Any, Optional
from ..models.base import ModelDefinition
from ..models.capabilities import ModelCapabilities, ModelPricing


def validate_model_definition(definition: ModelDefinition) -> bool:
    """验证模型定义"""
    try:
        # 基本信息验证
        _validate_basic_info(definition)
        
        # 能力定义验证
        if definition.capabilities:
            _validate_capabilities(definition.capabilities)
        
        # 定价信息验证
        if definition.pricing:
            _validate_pricing(definition.pricing)
        
        # 元数据验证
        if definition.metadata:
            _validate_metadata(definition.metadata)
        
        return True
    
    except ValueError as e:
        print(f"Validation error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected validation error: {e}")
        return False


def validate_capabilities(capabilities: ModelCapabilities) -> bool:
    """验证模型能力"""
    try:
        _validate_capabilities(capabilities)
        return True
    except ValueError as e:
        print(f"Capabilities validation error: {e}")
        return False


def validate_pricing(pricing: ModelPricing) -> bool:
    """验证模型定价"""
    try:
        _validate_pricing(pricing)
        return True
    except ValueError as e:
        print(f"Pricing validation error: {e}")
        return False


def _validate_basic_info(definition: ModelDefinition) -> None:
    """验证基本信息"""
    # ID验证
    if not definition.id or not isinstance(definition.id, str):
        raise ValueError("id must be a non-empty string")
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', definition.id):
        raise ValueError("id must contain only alphanumeric characters, underscores, and hyphens")
    
    # 提供商验证
    if not definition.provider or not isinstance(definition.provider, str):
        raise ValueError("provider must be a non-empty string")
    
    # 模型名称验证
    if not definition.name or not isinstance(definition.name, str):
        raise ValueError("name must be a non-empty string")
    
    # 显示名称验证
    if not definition.display_name or not isinstance(definition.display_name, str):
        raise ValueError("display_name must be a non-empty string")
    
    # 模型类型验证
    valid_types = ["chat", "completion", "embedding", "image", "audio", "video"]
    if definition.model_type not in valid_types:
        raise ValueError(f"model_type must be one of: {', '.join(valid_types)}")
    
    # 版本验证
    if definition.version and not isinstance(definition.version, str):
        raise ValueError("version must be a string")
    
    # 描述验证
    if definition.description and not isinstance(definition.description, str):
        raise ValueError("description must be a string")


def _validate_capabilities(capabilities: ModelCapabilities) -> None:
    """验证模型能力"""
    # 最大token数验证
    if not isinstance(capabilities.max_tokens, int) or capabilities.max_tokens <= 0:
        raise ValueError("max_tokens must be a positive integer")
    
    # 上下文窗口验证
    if not isinstance(capabilities.context_window, int) or capabilities.context_window <= 0:
        raise ValueError("context_window must be a positive integer")
    
    if capabilities.context_window > capabilities.max_tokens:
        raise ValueError("context_window cannot exceed max_tokens")
    
    # 布尔值验证
    bool_fields = [
        "supports_streaming", "supports_function_calling", "supports_code_generation",
        "supports_code_review", "supports_embedding", "supports_image_analysis"
    ]
    
    for field in bool_fields:
        value = getattr(capabilities, field)
        if not isinstance(value, bool):
            raise ValueError(f"{field} must be a boolean")
    
    # 响应速度验证
    if capabilities.response_speed is not None:
        valid_speeds = ["fast", "medium", "slow"]
        if capabilities.response_speed not in valid_speeds:
            raise ValueError(f"response_speed must be one of: {', '.join(valid_speeds)}")
    
    # 并发请求数验证
    if capabilities.concurrent_requests is not None:
        if not isinstance(capabilities.concurrent_requests, int) or capabilities.concurrent_requests <= 0:
            raise ValueError("concurrent_requests must be a positive integer")
    
    # 自定义能力验证
    if capabilities.custom_capabilities is not None:
        if not isinstance(capabilities.custom_capabilities, dict):
            raise ValueError("custom_capabilities must be a dictionary")


def _validate_pricing(pricing: ModelPricing) -> None:
    """验证模型定价"""
    # 输入成本验证
    if not isinstance(pricing.input_cost_per_1k, (int, float)) or pricing.input_cost_per_1k < 0:
        raise ValueError("input_cost_per_1k must be a non-negative number")
    
    # 输出成本验证
    if not isinstance(pricing.output_cost_per_1k, (int, float)) or pricing.output_cost_per_1k < 0:
        raise ValueError("output_cost_per_1k must be a non-negative number")
    
    # 货币验证
    if not pricing.currency or not isinstance(pricing.currency, str):
        raise ValueError("currency must be a non-empty string")
    
    # 货币代码格式验证（3位大写字母）
    if not re.match(r'^[A-Z]{3}$', pricing.currency):
        raise ValueError("currency must be a 3-letter uppercase code (e.g., USD, EUR)")
    
    # 月度配额验证
    if pricing.monthly_quota is not None:
        if not isinstance(pricing.monthly_quota, int) or pricing.monthly_quota <= 0:
            raise ValueError("monthly_quota must be a positive integer")
    
    # 免费额度验证
    if pricing.free_tier_limit is not None:
        if not isinstance(pricing.free_tier_limit, int) or pricing.free_tier_limit < 0:
            raise ValueError("free_tier_limit must be a non-negative integer")
    
    # 企业定价验证
    if pricing.enterprise_pricing is not None:
        if not isinstance(pricing.enterprise_pricing, dict):
            raise ValueError("enterprise_pricing must be a dictionary")


def _validate_metadata(metadata: Dict[str, Any]) -> None:
    """验证元数据"""
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be a dictionary")
    
    # 检查元数据键名
    for key in metadata.keys():
        if not isinstance(key, str):
            raise ValueError("metadata keys must be strings")
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', key):
            raise ValueError("metadata keys must contain only alphanumeric characters, underscores, and hyphens")


def validate_model_list(models: List[ModelDefinition]) -> List[str]:
    """验证模型列表，返回错误信息"""
    errors = []
    
    # 检查ID唯一性
    ids = set()
    for i, model in enumerate(models):
        if model.id in ids:
            errors.append(f"Duplicate model ID '{model.id}' at index {i}")
        ids.add(model.id)
    
    # 验证每个模型
    for i, model in enumerate(models):
        try:
            if not validate_model_definition(model):
                errors.append(f"Invalid model definition at index {i}: {model.id}")
        except Exception as e:
            errors.append(f"Error validating model at index {i} ({model.id}): {e}")
    
    return errors


def get_validation_summary(models: List[ModelDefinition]) -> Dict[str, Any]:
    """获取验证摘要"""
    total_models = len(models)
    valid_models = 0
    invalid_models = 0
    errors = []
    
    for model in models:
        if validate_model_definition(model):
            valid_models += 1
        else:
            invalid_models += 1
            errors.append(f"Invalid model: {model.id}")
    
    return {
        "total_models": total_models,
        "valid_models": valid_models,
        "invalid_models": invalid_models,
        "validation_errors": errors,
        "success_rate": (valid_models / total_models * 100) if total_models > 0 else 0
    }
