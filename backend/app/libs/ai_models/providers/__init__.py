"""
模型提供商定义

各个AI提供商的模型定义，每个文件包含该提供商的所有模型。
"""

from .deepseek import DEEPSEEK_MODELS
from .openai import OPENAI_MODELS
from .claude import CLAUDE_MODELS

__all__ = [
    "DEEPSEEK_MODELS",
    "OPENAI_MODELS", 
    "CLAUDE_MODELS"
]
