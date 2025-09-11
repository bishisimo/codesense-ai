"""
GitLabX 异常类
"""


class GitLabError(Exception):
    """GitLab API 基础异常"""
    pass


class GitLabConnectionError(GitLabError):
    """GitLab 连接异常"""
    pass


class GitLabAuthError(GitLabError):
    """GitLab 认证异常"""
    pass


class GitLabPermissionError(GitLabError):
    """GitLab 权限异常"""
    pass


class GitLabNotFoundError(GitLabError):
    """GitLab 资源不存在异常"""
    pass


class GitLabRateLimitError(GitLabError):
    """GitLab API 限流异常"""
    pass
