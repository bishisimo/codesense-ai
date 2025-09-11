"""
文件过滤器抽象基类
"""
from abc import ABC, abstractmethod
from typing import List


class BaseFileFilter(ABC):
    """文件过滤器抽象基类"""
    
    def __init__(self):
        """初始化文件过滤器"""
        pass
    
    @abstractmethod
    def should_ignore_file(self, file_path: str) -> bool:
        """
        判断是否应该忽略指定文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            True表示应该忽略，False表示不应该忽略
        """
        pass
    
    @abstractmethod
    def get_filter_description(self) -> str:
        """
        获取过滤器描述
        
        Returns:
            过滤器描述字符串
        """
        pass
    
    def filter_file_list(self, file_list: List[str]) -> List[str]:
        """
        过滤文件列表，返回需要审查的文件
        
        Args:
            file_list: 原始文件列表
            
        Returns:
            过滤后的文件列表
        """
        if not file_list:
            return []
        
        filtered_files = []
        for file_path in file_list:
            if not self.should_ignore_file(file_path):
                filtered_files.append(file_path)
        
        return filtered_files
    
    def get_ignored_files(self, file_list: List[str]) -> List[str]:
        """
        获取被忽略的文件列表
        
        Args:
            file_list: 原始文件列表
            
        Returns:
            被忽略的文件列表
        """
        if not file_list:
            return []
        
        ignored_files = []
        for file_path in file_list:
            if self.should_ignore_file(file_path):
                ignored_files.append(file_path)
        
        return ignored_files
    
    def __add__(self, other):
        """
        重载+操作符，支持过滤器合并
        
        Args:
            other: 另一个过滤器实例
            
        Returns:
            合并后的过滤器实例
        """
        if not isinstance(other, BaseFileFilter):
            raise TypeError("只能与BaseFileFilter实例进行合并")
        
        # 创建合并后的过滤器实例
        merged_filter = self.__class__()
        return merged_filter
