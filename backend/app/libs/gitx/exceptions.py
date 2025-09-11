"""
Git操作相关异常
"""


class GitError(Exception):
    """Git操作基础异常"""
    pass


class RepositoryNotFoundError(GitError):
    """仓库未找到异常"""
    pass


class GitCommandError(GitError):
    """Git命令执行错误"""
    
    def __init__(self, message: str, cmd: str = None, stderr: str = None):
        super().__init__(message)
        self.cmd = cmd
        self.stderr = stderr
    
    def __str__(self):
        result = super().__str__()
        if self.cmd:
            result += f" (命令: {self.cmd})"
        if self.stderr:
            result += f" (错误输出: {self.stderr})"
        return result


class BranchNotFoundError(GitError):
    """分支未找到异常"""
    pass


class CommitNotFoundError(GitError):
    """提交未找到异常"""
    pass


class UncommittedChangesError(GitError):
    """存在未提交的变更异常"""
    pass

