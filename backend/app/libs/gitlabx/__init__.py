"""
GitLabX - GitLab API 封装库
"""
from .client import GitLabClient
from .models import ProjectInfo, MergeRequestInfo, PaginationInfo
from .exceptions import GitLabError, GitLabConnectionError, GitLabAuthError

__all__ = [
    "GitLabClient",
    "ProjectInfo",
    "MergeRequestInfo", 
    "PaginationInfo",
    "GitLabError",
    "GitLabConnectionError",
    "GitLabAuthError",
]
