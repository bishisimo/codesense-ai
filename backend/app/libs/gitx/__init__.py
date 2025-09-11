"""
GitPython封装库

提供简化的Git操作接口
"""

from .client import GitClient
from .models import CommitInfo, DiffInfo, BranchInfo, FileChange
from .exceptions import GitError, RepositoryNotFoundError, GitCommandError

__all__ = [
    "GitClient",
    "CommitInfo",
    "DiffInfo", 
    "BranchInfo",
    "FileChange",
    "GitError",
    "RepositoryNotFoundError",
    "GitCommandError"
]

