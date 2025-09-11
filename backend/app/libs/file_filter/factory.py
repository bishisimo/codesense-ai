"""
文件过滤器工厂类
"""
from typing import Dict, Optional, Any
from .base import BaseFileFilter
from .default import DefaultFileFilter
from .language import GoFileFilter


class FileFilterFactory:
    """文件过滤器工厂类"""
    
    # 注册的过滤器类型
    _filters: Dict[str, type] = {
        "default": DefaultFileFilter,
        "go": GoFileFilter,
    }
    
    @classmethod
    def create_filter(cls, language: Optional[str] = None) -> BaseFileFilter:
        """
        创建文件过滤器实例
        
        Args:
            language: 编程语言，如果指定则返回语言特定的过滤器
            
        Returns:
            文件过滤器实例
        """
        # 如果没有指定语言或语言不支持，使用默认过滤器
        if not language or language.lower() not in cls._filters:
            language = "default"
        
        filter_class = cls._filters[language.lower()]
        return filter_class()
    
    @classmethod
    def register_filter(cls, language: str, filter_class: type) -> None:
        """
        注册新的过滤器类型
        
        Args:
            language: 语言名称
            filter_class: 过滤器类
        """
        if not issubclass(filter_class, BaseFileFilter):
            raise ValueError("过滤器类必须继承自BaseFileFilter")
        
        cls._filters[language.lower()] = filter_class
    
    @classmethod
    def unregister_filter(cls, language: str) -> None:
        """
        取消注册过滤器类型
        
        Args:
            language: 语言名称
        """
        if language.lower() in cls._filters and language.lower() != "default":
            del cls._filters[language.lower()]
    
    @classmethod
    def get_available_languages(cls) -> list:
        """
        获取可用的语言列表
        
        Returns:
            可用语言列表
        """
        return list(cls._filters.keys())
    
    @classmethod
    def get_filter_info(cls, language: str) -> Dict[str, Any]:
        """
        获取过滤器信息
        
        Args:
            language: 语言名称
            
        Returns:
            过滤器信息字典
        """
        if language.lower() not in cls._filters:
            return {"error": f"不支持的语言: {language}"}
        
        filter_class = cls._filters[language.lower()]
        filter_instance = filter_class()
        
        return {
            "language": language,
            "class_name": filter_class.__name__,
            "description": filter_instance.get_filter_description(),
            "ignored_files_count": len(filter_instance.ignored_files),
            "ignored_directories_count": len(filter_instance.ignored_directories)
        }
    
    @classmethod
    def list_all_filters(cls) -> Dict[str, Dict[str, Any]]:
        """
        列出所有可用的过滤器信息
        
        Returns:
            所有过滤器信息字典
        """
        result = {}
        for language in cls._filters.keys():
            result[language] = cls.get_filter_info(language)
        return result
    
