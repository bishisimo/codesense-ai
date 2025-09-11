"""
语言特定的文件过滤器实现
"""
from typing import List
from .base import BaseFileFilter


class GoFileFilter(BaseFileFilter):
    """Go项目文件过滤器"""
    
    def __init__(self):
        """初始化Go文件过滤器"""
        super().__init__()
        self.ignored_files = self._get_go_ignored_files()
        self.ignored_directories = self._get_go_ignored_directories()
    
    def _get_go_ignored_files(self) -> List[str]:
        """获取Go项目要忽略的文件列表"""
        return [
            # Go特定文件
            "go.mod", "go.sum", "*.exe", "*.dll", "*.so", "*.dylib",
            # 依赖管理文件
            "vendor/*", "Gopkg.lock", "Gopkg.toml",
            # 文档文件
            "*.md", "*.txt", "*.log",
            # 配置文件
            "*.yaml", "*.yml", "*.json", "*.toml", "*.ini",
            # 测试相关
            "*.test", "*.out", "coverage.out", "coverage.html",
            # 构建产物
            "*.a", "*.lib", "*.o", "*.obj",
        ]
    
    def _get_go_ignored_directories(self) -> List[str]:
        """获取Go项目要忽略的目录列表"""
        return [
            # Go特定目录
            "vendor", "pkg", "bin", "obj",
            # 构建输出目录
            "dist", "build", "target", "out",
            # 依赖目录
            "node_modules",
            # 版本控制目录
            ".git", ".svn", ".hg", ".bzr",
            # IDE配置目录
            ".idea", ".vscode", ".vs", ".eclipse", ".settings",
            # 操作系统目录
            ".DS_Store", "Thumbs.db", "desktop.ini",
        ]
    
    def should_ignore_file(self, file_path: str) -> bool:
        """
        判断是否应该忽略指定文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            True表示应该忽略，False表示不应该忽略
        """
        if not file_path:
            return True
        
        # 标准化路径分隔符
        normalized_path = file_path.replace('\\', '/')
        
        # 检查目录
        path_parts = normalized_path.split('/')
        for part in path_parts:
            if part in self.ignored_directories:
                return True
        
        # 检查文件
        import fnmatch
        for pattern in self.ignored_files:
            if fnmatch.fnmatch(normalized_path, pattern):
                return True
        
        return False
    
    def get_filter_description(self) -> str:
        """
        获取过滤器描述
        
        Returns:
            过滤器描述字符串
        """
        return "Go项目文件过滤器，自动过滤Go特定的不需要审查的文件"