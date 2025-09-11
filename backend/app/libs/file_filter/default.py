"""
默认文件过滤器实现
"""
from typing import List
from .base import BaseFileFilter


class DefaultFileFilter(BaseFileFilter):
    """默认文件过滤器 - 适用于大多数项目"""
    
    def __init__(self):
        """初始化默认文件过滤器"""
        super().__init__()
        self.ignored_files = self._get_default_ignored_files()
        self.ignored_directories = self._get_default_ignored_directories()
    
    def _get_default_ignored_files(self) -> List[str]:
        """获取默认要忽略的文件列表"""
        return [
            # 文档文件
            "*.md", "*.txt", "*.rst", "*.adoc", "*.tex", "*.pdf",
            # 日志文件
            "*.log", "*.out", "*.err",
            # 配置文件
            "*.json", "*.xml", "*.ini", "*.conf",
            "*.config", "*.properties", "*.env", "*.example",
            # 依赖管理文件
            "go.mod", "go.sum", "package.json", "package-lock.json", 
            "yarn.lock", "*.lock", "requirements.txt", "Pipfile", 
            "Pipfile.lock", "poetry.lock", "Gemfile", "Gemfile.lock",
            "composer.json", "composer.lock", "Cargo.toml", "Cargo.lock",
            # 构建产物
            "*.min.js", "*.min.css", "*.bundle.js", "*.bundle.css",
            "*.map", "*.o", "*.obj", "*.exe", "*.dll", "*.so", "*.dylib",
            "*.a", "*.lib", "*.class", "*.jar", "*.war", "*.ear",
            # 图片和媒体文件
            "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.ico",
            "*.bmp", "*.tiff", "*.webp", "*.mp4", "*.avi", "*.mov",
            "*.wmv", "*.flv", "*.webm", "*.mp3", "*.wav", "*.flac",
            # 字体文件
            "*.woff", "*.woff2", "*.ttf", "*.eot", "*.otf",
            # 压缩文件
            "*.zip", "*.tar", "*.gz", "*.rar", "*.7z", "*.bz2",
            # 临时文件
            "*.tmp", "*.temp", "*.bak", "*.backup", "*.orig", "*.rej",
            "*.swp", "*.swo", "*.patch", "*.diff",
            # 数据库文件
            "*.db", "*.sqlite", "*.sqlite3", "*.mdb", "*.accdb",
            # 其他二进制文件
            "*.bin", "*.dat", "*.dump", "*.cache",
        ]
    
    def _get_default_ignored_directories(self) -> List[str]:
        """获取默认要忽略的目录列表"""
        return [
            # 版本控制目录
            ".git", ".svn", ".hg", ".bzr",
            # 依赖目录
            "node_modules", "vendor", "bower_components", "jspm_packages",
            "__pycache__", ".pytest_cache", ".mypy_cache", ".coverage",
            # 构建输出目录
            "dist", "build", "target", "out", "bin", "obj", "lib",
            "coverage", "reports", "logs", "tmp", "temp",
            # IDE配置目录
            ".idea", ".vscode", ".vs", ".eclipse", ".settings",
            # 操作系统目录
            ".DS_Store", "Thumbs.db", "desktop.ini",
            # 其他
            ".next", ".nuxt", ".cache", ".parcel-cache", ".turbo",
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
        return "默认文件过滤器，自动过滤文档、配置、依赖、构建产物等不需要审查的文件"
