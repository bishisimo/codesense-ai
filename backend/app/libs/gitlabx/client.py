"""
GitLabX 客户端
"""
import gitlab
from typing import List, Optional, Iterator, Tuple, Dict, Any
from urllib.parse import urlparse

from .models import ProjectInfo, MergeRequestInfo, CommitInfo, PaginationInfo, FileChangeInfo
from .exceptions import (
    GitLabError,
    GitLabConnectionError,
    GitLabAuthError,
    GitLabPermissionError,
    GitLabNotFoundError,
    GitLabRateLimitError,
)
from app.core.logging import get_logger

logger = get_logger("gitlab_client")


class GitLabClient:
    """GitLab API 客户端封装"""
    
    def __init__(self, url: str, token: str, timeout: int = 30):
        """
        初始化GitLab客户端
        
        Args:
            url: GitLab实例URL
            token: 访问令牌
            timeout: 请求超时时间
        """
        self.url = self._normalize_url(url)
        self.token = token
        self.timeout = timeout
        
        try:
            self._client = gitlab.Gitlab(
                url=self.url,
                private_token=token,
                timeout=timeout,
                retry_transient_errors=True,
            )
            # 测试连接
            self._client.auth()
        except gitlab.GitlabAuthenticationError as e:
            raise GitLabAuthError(f"GitLab认证失败: {e}")
        except gitlab.GitlabError as e:
            raise GitLabConnectionError(f"GitLab连接失败: {e}")
        except Exception as e:
            raise GitLabError(f"GitLab初始化失败: {e}")
    
    def _normalize_url(self, url: str) -> str:
        """标准化URL格式"""
        if not url.startswith(('http://', 'https://')):
            url = f"http://{url}"
        
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _handle_gitlab_error(self, e: Exception) -> None:
        """处理GitLab异常"""
        if isinstance(e, gitlab.GitlabAuthenticationError):
            raise GitLabAuthError(f"认证失败: {e}")
        elif isinstance(e, gitlab.GitlabGetError):
            if e.response_code == 404:
                raise GitLabNotFoundError(f"资源不存在: {e}")
            elif e.response_code == 403:
                raise GitLabPermissionError(f"权限不足: {e}")
            elif e.response_code == 429:
                raise GitLabRateLimitError(f"API限流: {e}")
            else:
                raise GitLabError(f"获取失败: {e}")
        elif isinstance(e, gitlab.GitlabError):
            raise GitLabError(f"GitLab API错误: {e}")
        else:
            raise GitLabError(f"未知错误: {e}")
    
    # 项目相关方法
    def get_projects(
        self, 
        page: int = 1, 
        per_page: int = 100,
        owned: bool = False,
        membership: bool = True,
        search: Optional[str] = None,
        visibility: Optional[str] = None,
    ) -> Tuple[List[ProjectInfo], PaginationInfo]:
        """
        获取项目列表
        
        Args:
            page: 页码
            per_page: 每页数量
            owned: 仅获取拥有的项目
            membership: 获取有成员权限的项目
            search: 搜索关键词
            visibility: 可见性过滤 (public, internal, private)
            
        Returns:
            (项目列表, 分页信息)
        """
        try:
            kwargs = {
                'page': page,
                'per_page': per_page,
                'owned': owned,
                'membership': membership,
            }
            
            if search:
                kwargs['search'] = search
            if visibility:
                kwargs['visibility'] = visibility
            
            projects = self._client.projects.list(**kwargs, lazy=False)
            
            # 构建分页信息
            pagination = PaginationInfo(
                page=page,
                per_page=per_page,
                total_pages=getattr(projects, 'total_pages', None),
                total_items=getattr(projects, 'total', None),
                has_next=hasattr(projects, 'next_url') and projects.next_url is not None,
            )
            
            # 转换为ProjectInfo对象
            project_infos = []
            for project in projects:
                try:
                    project_info = ProjectInfo.from_gitlab_project(project)
                    project_infos.append(project_info)
                except Exception as e:
                    logger.warning(f"转换项目信息失败 {project.name}: {e}")
                    continue
            
            return project_infos, pagination
            
        except Exception as e:
            self._handle_gitlab_error(e)
    
    def get_project(self, project_id: int) -> ProjectInfo:
        """
        获取单个项目信息
        
        Args:
            project_id: 项目ID
            
        Returns:
            项目信息
        """
        try:
            project = self._client.projects.get(project_id)
            return ProjectInfo.from_gitlab_project(project)
        except Exception as e:
            self._handle_gitlab_error(e)
    
    def get_project_by_path(self, project_path: str) -> ProjectInfo:
        """
        通过路径获取项目信息
        
        Args:
            project_path: 项目路径 (如 namespace/project)
            
        Returns:
            项目信息
        """
        try:
            project = self._client.projects.get(project_path, lazy=False)
            return ProjectInfo.from_gitlab_project(project)
        except Exception as e:
            self._handle_gitlab_error(e)
    
    # 合并请求相关方法
    def get_merge_requests(
        self,
        project_id: int,
        state: str = "opened",
        page: int = 1,
        per_page: int = 100,
        order_by: str = "created_at",
        sort: str = "desc",
        source_branch: Optional[str] = None,
        target_branch: Optional[str] = None,
        author_id: Optional[int] = None,
    ) -> Tuple[List[MergeRequestInfo], PaginationInfo]:
        """
        获取合并请求列表
        
        Args:
            project_id: 项目ID
            state: 状态 (opened, closed, merged, all)
            page: 页码
            per_page: 每页数量
            order_by: 排序字段 (created_at, updated_at, title)
            sort: 排序方向 (asc, desc)
            source_branch: 源分支
            target_branch: 目标分支
            author_id: 作者ID
            
        Returns:
            (合并请求列表, 分页信息)
        """
        try:
            project = self._client.projects.get(project_id, lazy=True)
            
            kwargs = {
                'state': state,
                'page': page,
                'per_page': per_page,
                'order_by': order_by,
                'sort': sort,
            }
            
            if source_branch:
                kwargs['source_branch'] = source_branch
            if target_branch:
                kwargs['target_branch'] = target_branch
            if author_id:
                kwargs['author_id'] = author_id
            
            merge_requests = project.mergerequests.list(**kwargs, lazy=False)
            
            # 构建分页信息
            pagination = PaginationInfo(
                page=page,
                per_page=per_page,
                total_pages=getattr(merge_requests, 'total_pages', None),
                total_items=getattr(merge_requests, 'total', None),
                has_next=hasattr(merge_requests, 'next_url') and merge_requests.next_url is not None,
            )
            
            # 转换为MergeRequestInfo对象
            mr_infos = []
            for mr in merge_requests:
                try:
                    # 直接使用列表中的MR信息，避免额外的API调用
                    mr_info = MergeRequestInfo.from_gitlab_mr(mr)
                    
                    mr_infos.append(mr_info)
                except Exception as e:
                    logger.warning(f"转换合并请求信息失败 {mr.title}: {e}")
                    continue
            
            return mr_infos, pagination
            
        except Exception as e:
            self._handle_gitlab_error(e)
    
    def get_merge_request(self, project_id: int, mr_iid: int) -> MergeRequestInfo:
        """
        获取单个合并请求信息
        
        Args:
            project_id: 项目ID
            mr_iid: 合并请求IID
            
        Returns:
            合并请求信息
        """
        try:
            project = self._client.projects.get(project_id, lazy=True)
            mr = project.mergerequests.get(mr_iid)
            return MergeRequestInfo.from_gitlab_mr(mr)
        except Exception as e:
            self._handle_gitlab_error(e)
    
    def get_merge_request_changes(
        self, 
        project_id: int, 
        mr_iid: int
    ) -> List[FileChangeInfo]:
        """
        获取合并请求的文件变更
        
        Args:
            project_id: 项目ID
            mr_iid: 合并请求IID
            
        Returns:
            文件变更列表
        """
        try:
            project = self._client.projects.get(project_id, lazy=True)
            mr = project.mergerequests.get(mr_iid)
            changes = mr.changes()
            
            file_changes = []
            for change in changes.get('changes', []):
                file_change = FileChangeInfo(
                    old_path=change.get('old_path'),
                    new_path=change.get('new_path'),
                    new_file=change.get('new_file', False),
                    renamed_file=change.get('renamed_file', False),
                    deleted_file=change.get('deleted_file', False),
                    diff=change.get('diff', ''),
                )
                file_changes.append(file_change)
            
            return file_changes
            
        except Exception as e:
            self._handle_gitlab_error(e)
    
    def get_merge_request_commits(
        self, 
        project_id: int, 
        mr_iid: int
    ) -> List[CommitInfo]:
        """
        获取合并请求的提交列表
        
        Args:
            project_id: 项目ID
            mr_iid: 合并请求IID
            
        Returns:
            提交列表
        """
        try:
            project = self._client.projects.get(project_id, lazy=True)
            mr = project.mergerequests.get(mr_iid)
            commits = mr.commits()
            
            commit_infos = []
            for commit in commits:
                try:
                    commit_info = CommitInfo.from_gitlab_commit(commit)
                    commit_infos.append(commit_info)
                except Exception as e:
                    logger.warning(f"转换提交信息失败 {commit.id}: {e}")
                    continue
            
            return commit_infos
            
        except Exception as e:
            self._handle_gitlab_error(e)

    def get_merge_request_changes_stats(
        self, 
        project_id: int, 
        mr_iid: int
    ) -> Dict[str, int]:
        """
        获取合并请求的变更统计信息
        
        Args:
            project_id: 项目ID
            mr_iid: 合并请求IID
            
        Returns:
            变更统计信息 {'additions': 新增行数, 'deletions': 删除行数, 'total': 总变更行数}
        """
        try:
            project = self._client.projects.get(project_id, lazy=True)
            mr = project.mergerequests.get(mr_iid)
            changes = mr.changes().get('changes', [])
            
            total_additions = 0
            total_deletions = 0
            
            for change in changes:
                diff = change.get('diff', '')
                if diff:
                    # 解析diff统计行数
                    additions = 0
                    deletions = 0
                    
                    for line in diff.split('\n'):
                        if line.startswith('+') and not line.startswith('+++'):
                            additions += 1
                        elif line.startswith('-') and not line.startswith('---'):
                            deletions += 1
                    
                    total_additions += additions
                    total_deletions += deletions
            
            return {
                'additions': total_additions,
                'deletions': total_deletions,
                'total': total_additions + total_deletions
            }
            
        except Exception as e:
            self._handle_gitlab_error(e)
    
    def create_merge_request_note(
        self,
        project_id: int,
        mr_iid: int,
        body: str,
    ) -> Dict[str, Any]:
        """
        在合并请求中创建评论
        
        Args:
            project_id: 项目ID
            mr_iid: 合并请求IID
            body: 评论内容
            
        Returns:
            评论信息
        """
        try:
            project = self._client.projects.get(project_id, lazy=True)
            mr = project.mergerequests.get(mr_iid)
            note = mr.notes.create({'body': body})
            
            return {
                'id': note.id,
                'body': note.body,
                'author': note.author,
                'created_at': note.created_at,
                'updated_at': note.updated_at,
            }
            
        except Exception as e:
            self._handle_gitlab_error(e)
    
    def get_file_content(
        self, 
        project_id: int, 
        file_path: str, 
        ref: str = "main"
    ) -> str:
        """
        获取文件内容
        
        Args:
            project_id: 项目ID
            file_path: 文件路径
            ref: 分支或提交ID
            
        Returns:
            文件内容
        """
        try:
            project = self._client.projects.get(project_id, lazy=True)
            file = project.files.get(file_path=file_path, ref=ref)
            return file.decode().decode('utf-8')
        except Exception as e:
            self._handle_gitlab_error(e)
    
    def get_repository_tree(
        self,
        project_id: int,
        path: str = "",
        ref: str = "main",
        recursive: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        获取仓库目录树
        
        Args:
            project_id: 项目ID
            path: 路径
            ref: 分支或提交ID
            recursive: 是否递归
            
        Returns:
            目录树列表
        """
        try:
            project = self._client.projects.get(project_id, lazy=True)
            tree = project.repository_tree(
                path=path,
                ref=ref,
                recursive=recursive,
                all=True,
            )
            
            return [
                {
                    'id': item['id'],
                    'name': item['name'],
                    'type': item['type'],
                    'path': item['path'],
                    'mode': item['mode'],
                }
                for item in tree
            ]
            
        except Exception as e:
            self._handle_gitlab_error(e)
    
    def iter_all_projects(
        self,
        per_page: int = 100,
        **kwargs
    ) -> Iterator[ProjectInfo]:
        """
        迭代获取所有项目
        
        Args:
            per_page: 每页数量
            **kwargs: 其他过滤参数
            
        Yields:
            项目信息
        """
        page = 1
        while True:
            try:
                projects, pagination = self.get_projects(
                    page=page,
                    per_page=per_page,
                    **kwargs
                )
                
                for project in projects:
                    yield project
                
                if not pagination.has_next:
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"迭代项目失败 (page {page}): {e}")
                break
    
    def iter_all_merge_requests(
        self,
        project_id: int,
        per_page: int = 100,
        **kwargs
    ) -> Iterator[MergeRequestInfo]:
        """
        迭代获取项目的所有合并请求
        
        Args:
            project_id: 项目ID
            per_page: 每页数量
            **kwargs: 其他过滤参数
            
        Yields:
            合并请求信息
        """
        page = 1
        while True:
            try:
                merge_requests, pagination = self.get_merge_requests(
                    project_id=project_id,
                    page=page,
                    per_page=per_page,
                    **kwargs
                )
                
                for mr in merge_requests:
                    yield mr
                
                if not pagination.has_next:
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"迭代合并请求失败 (page {page}): {e}")
                break
    
    def test_connection(self) -> bool:
        """
        测试GitLab连接
        
        Returns:
            连接是否成功
        """
        try:
            user = self._client.user
            logger.info(f"GitLab连接成功，当前用户: {user.username}")
            return True
        except Exception as e:
            logger.error(f"GitLab连接失败: {e}")
            return False
