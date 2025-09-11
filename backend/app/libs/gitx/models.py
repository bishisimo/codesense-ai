"""
Git相关数据模型
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class CommitInfo:
    """提交信息"""
    sha: str
    author_name: str
    author_email: str
    committer_name: str
    committer_email: str
    message: str
    authored_date: datetime
    committed_date: datetime
    parents: List[str]
    
    @property
    def short_sha(self) -> str:
        """获取短SHA"""
        return self.sha[:8] if self.sha else ""
    
    @property
    def title(self) -> str:
        """获取提交标题（第一行）"""
        return self.message.split('\n')[0] if self.message else ""
    
    @property
    def body(self) -> str:
        """获取提交正文（除第一行外的内容）"""
        lines = self.message.split('\n')
        return '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""


@dataclass
class FileChange:
    """文件变更信息"""
    file_path: str
    change_type: str  # A: added, M: modified, D: deleted, R: renamed
    old_path: Optional[str] = None  # 重命名时的原路径
    additions: int = 0
    deletions: int = 0
    binary: bool = False


@dataclass
class DiffInfo:
    """差异信息"""
    commit_sha: str
    base_sha: Optional[str]
    files: List[FileChange]
    additions: int
    deletions: int
    
    @property
    def total_changes(self) -> int:
        """总变更行数"""
        return self.additions + self.deletions


@dataclass
class BranchInfo:
    """分支信息"""
    name: str
    commit_sha: str
    is_current: bool = False
    is_remote: bool = False
    remote_name: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """获取完整分支名"""
        if self.is_remote and self.remote_name:
            return f"{self.remote_name}/{self.name}"
        return self.name


@dataclass
class RepositoryInfo:
    """仓库信息"""
    path: str
    current_branch: str
    remote_url: Optional[str]
    head_commit: CommitInfo
    is_dirty: bool = False
    untracked_files: List[str] = None
    
    def __post_init__(self):
        if self.untracked_files is None:
            self.untracked_files = []


@dataclass
class TagInfo:
    """标签信息"""
    name: str
    commit_sha: str
    message: Optional[str] = None
    tagger_name: Optional[str] = None
    tagger_email: Optional[str] = None
    tagged_date: Optional[datetime] = None


@dataclass
class MergeInfo:
    """合并信息"""
    source_branch: str
    target_branch: str
    merge_commit: Optional[str] = None
    conflicts: List[str] = None
    
    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []

