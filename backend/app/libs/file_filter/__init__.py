"""
文件过滤器包 - 用于过滤代码审查中不需要的文件
"""

from .base import BaseFileFilter
from .default import DefaultFileFilter
from .language import GoFileFilter
from .factory import FileFilterFactory

__all__ = [
    'BaseFileFilter',
    'DefaultFileFilter',
    'GoFileFilter',
    'FileFilterFactory'
]

# 便捷函数
def get_file_filter(language: str = None) -> BaseFileFilter:
    """
    获取文件过滤器实例
    
    Args:
        language: 编程语言，如果指定则返回语言特定的过滤器
        
    Returns:
        文件过滤器实例
    """
    return FileFilterFactory.create_filter(language)

