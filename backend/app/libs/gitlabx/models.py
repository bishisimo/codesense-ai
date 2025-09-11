"""
GitLabX 数据模型
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class PaginationInfo(BaseModel):
    """分页信息"""
    page: int = Field(default=1, description="当前页码")
    per_page: int = Field(default=20, description="每页数量")
    total_pages: Optional[int] = Field(default=None, description="总页数")
    total_items: Optional[int] = Field(default=None, description="总条目数")
    has_next: bool = Field(default=False, description="是否有下一页")


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    username: str
    name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None


class NamespaceInfo(BaseModel):
    """命名空间信息"""
    id: int
    name: str
    path: str
    kind: str
    full_path: str


class ProjectInfo(BaseModel):
    """项目信息"""
    id: int
    name: str
    path: str
    namespace: NamespaceInfo
    web_url: str
    description: Optional[str] = None
    default_branch: str = "main"
    visibility: str = "private"
    created_at: datetime
    updated_at: datetime
    last_activity_at: Optional[datetime] = None
    
    # 统计信息
    star_count: int = 0
    forks_count: int = 0
    issues_enabled: bool = True
    merge_requests_enabled: bool = True
    
    @classmethod
    def from_gitlab_project(cls, project: Any) -> "ProjectInfo":
        """从GitLab项目对象创建"""
        return cls(
            id=project.id,
            name=project.name,
            path=project.path,
            namespace=NamespaceInfo(
                id=project.namespace.get("id"),
                name=project.namespace.get("name"),
                path=project.namespace.get("path"),
                kind=project.namespace.get("kind", "user"),
                full_path=project.namespace.get("full_path"),
            ),
            web_url=project.web_url,
            description=project.description,
            default_branch=project.default_branch or "main",
            visibility=project.visibility,
            created_at=datetime.fromisoformat(project.created_at.replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(project.last_activity_at.replace('Z', '+00:00')) if project.last_activity_at else datetime.now(),
            last_activity_at=datetime.fromisoformat(project.last_activity_at.replace('Z', '+00:00')) if project.last_activity_at else None,
            star_count=getattr(project, 'star_count', 0),
            forks_count=getattr(project, 'forks_count', 0),
            issues_enabled=getattr(project, 'issues_enabled', True),
            merge_requests_enabled=getattr(project, 'merge_requests_enabled', True),
        )


class MergeRequestInfo(BaseModel):
    """合并请求信息"""
    id: int
    iid: int
    title: str
    description: Optional[str] = None
    state: str
    source_branch: str
    target_branch: str
    author: UserInfo
    assignee: Optional[UserInfo] = None
    reviewer: Optional[UserInfo] = None
    web_url: str
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # 状态信息
    work_in_progress: bool = False
    draft: bool = False
    has_conflicts: bool = False
    merge_status: str = "can_be_merged"
    
    # 统计信息
    upvotes: int = 0
    downvotes: int = 0
    user_notes_count: int = 0
    changes_count: Optional[int] = None
    commits_count: Optional[int] = None
    
    @classmethod
    def from_gitlab_mr(cls, mr: Any) -> "MergeRequestInfo":
        """从GitLab合并请求对象创建"""
        return cls(
            id=mr.id,
            iid=mr.iid,
            title=mr.title,
            description=mr.description,
            state=mr.state,
            source_branch=mr.source_branch,
            target_branch=mr.target_branch,
            author=UserInfo(
                id=mr.author["id"],
                username=mr.author["username"],
                name=mr.author["name"],
                email=mr.author.get("email"),
                avatar_url=mr.author.get("avatar_url"),
            ),
            assignee=UserInfo(
                id=mr.assignee["id"],
                username=mr.assignee["username"],
                name=mr.assignee["name"],
                email=mr.assignee.get("email"),
                avatar_url=mr.assignee.get("avatar_url"),
            ) if mr.assignee else None,
            web_url=mr.web_url,
            created_at=datetime.fromisoformat(mr.created_at.replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(mr.updated_at.replace('Z', '+00:00')),
            merged_at=datetime.fromisoformat(mr.merged_at.replace('Z', '+00:00')) if mr.merged_at else None,
            closed_at=datetime.fromisoformat(mr.closed_at.replace('Z', '+00:00')) if mr.closed_at else None,
            work_in_progress=getattr(mr, 'work_in_progress', False),
            draft=getattr(mr, 'draft', False),
            has_conflicts=getattr(mr, 'has_conflicts', False),
            merge_status=getattr(mr, 'merge_status', 'can_be_merged'),
            upvotes=getattr(mr, 'upvotes', 0),
            downvotes=getattr(mr, 'downvotes', 0),
            user_notes_count=getattr(mr, 'user_notes_count', 0),
            changes_count=getattr(mr, 'changes_count', None),
            commits_count=getattr(mr, 'commits_count', None),
        )


class CommitInfo(BaseModel):
    """提交信息"""
    id: str
    short_id: str
    title: str
    message: str
    author_name: str
    author_email: str
    authored_date: datetime
    committer_name: str
    committer_email: str
    committed_date: datetime
    web_url: str
    
    @classmethod
    def from_gitlab_commit(cls, commit: Any) -> "CommitInfo":
        """从GitLab提交对象创建"""
        return cls(
            id=commit.id,
            short_id=commit.short_id,
            title=commit.title,
            message=commit.message,
            author_name=commit.author_name,
            author_email=commit.author_email,
            authored_date=datetime.fromisoformat(commit.authored_date.replace('Z', '+00:00')),
            committer_name=commit.committer_name,
            committer_email=commit.committer_email,
            committed_date=datetime.fromisoformat(commit.committed_date.replace('Z', '+00:00')),
            web_url=commit.web_url,
        )


class FileChangeInfo(BaseModel):
    """文件变更信息"""
    old_path: Optional[str] = None
    new_path: str
    new_file: bool = False
    renamed_file: bool = False
    deleted_file: bool = False
    diff: str
