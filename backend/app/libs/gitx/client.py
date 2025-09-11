"""
GitPython客户端封装
"""
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

try:
    import git
    from git import Repo, InvalidGitRepositoryError, GitCommandError as GitPyCommandError
except ImportError:
    raise ImportError("请安装GitPython: pip install GitPython")

from .models import (
    CommitInfo, DiffInfo, BranchInfo, FileChange, 
    RepositoryInfo, TagInfo, MergeInfo
)
from .exceptions import (
    GitError, RepositoryNotFoundError, GitCommandError,
    BranchNotFoundError, CommitNotFoundError, UncommittedChangesError
)


class GitClient:
    """Git客户端封装"""
    
    def __init__(self, repo_path: str):
        """
        初始化Git客户端
        
        Args:
            repo_path: Git仓库路径
        """
        self.repo_path = Path(repo_path).resolve()
        self._repo = None
        self._init_repository()
    
    def _init_repository(self):
        """初始化仓库连接"""
        try:
            self._repo = Repo(str(self.repo_path))
        except InvalidGitRepositoryError:
            raise RepositoryNotFoundError(f"路径不是有效的Git仓库: {self.repo_path}")
        except Exception as e:
            raise GitError(f"初始化Git仓库失败: {str(e)}")
    
    @property
    def repo(self) -> Repo:
        """获取GitPython Repo对象"""
        if self._repo is None:
            self._init_repository()
        return self._repo
    
    def get_repository_info(self) -> RepositoryInfo:
        """获取仓库基本信息"""
        try:
            current_branch = self.repo.active_branch.name
        except:
            # 可能处于detached HEAD状态
            current_branch = "HEAD"
        
        # 获取远程URL
        remote_url = None
        try:
            if 'origin' in self.repo.remotes:
                remote_url = self.repo.remotes.origin.url
        except:
            pass
        
        # 获取HEAD提交
        head_commit = self.get_commit_info(self.repo.head.commit.hexsha)
        
        # 检查是否有未提交的变更
        is_dirty = self.repo.is_dirty(untracked_files=True)
        
        # 获取未跟踪的文件
        untracked_files = self.repo.untracked_files
        
        return RepositoryInfo(
            path=str(self.repo_path),
            current_branch=current_branch,
            remote_url=remote_url,
            head_commit=head_commit,
            is_dirty=is_dirty,
            untracked_files=list(untracked_files)
        )
    
    def get_commit_info(self, commit_sha: str) -> CommitInfo:
        """获取提交信息"""
        try:
            commit = self.repo.commit(commit_sha)
            
            return CommitInfo(
                sha=commit.hexsha,
                author_name=commit.author.name,
                author_email=commit.author.email,
                committer_name=commit.committer.name,
                committer_email=commit.committer.email,
                message=commit.message,
                authored_date=datetime.fromtimestamp(commit.authored_date),
                committed_date=datetime.fromtimestamp(commit.committed_date),
                parents=[p.hexsha for p in commit.parents]
            )
        except Exception as e:
            raise CommitNotFoundError(f"无法找到提交 {commit_sha}: {str(e)}")
    
    def get_commits(
        self, 
        branch: str = None, 
        limit: int = 100,
        since: datetime = None,
        until: datetime = None,
        author: str = None,
        paths: List[str] = None
    ) -> List[CommitInfo]:
        """获取提交列表"""
        try:
            # 构建参数
            kwargs = {}
            if limit:
                kwargs['max_count'] = limit
            if since:
                kwargs['since'] = since
            if until:
                kwargs['until'] = until
            if author:
                kwargs['author'] = author
            if paths:
                kwargs['paths'] = paths
            
            # 获取提交
            ref = branch or 'HEAD'
            commits = list(self.repo.iter_commits(ref, **kwargs))
            
            return [
                CommitInfo(
                    sha=commit.hexsha,
                    author_name=commit.author.name,
                    author_email=commit.author.email,
                    committer_name=commit.committer.name,
                    committer_email=commit.committer.email,
                    message=commit.message,
                    authored_date=datetime.fromtimestamp(commit.authored_date),
                    committed_date=datetime.fromtimestamp(commit.committed_date),
                    parents=[p.hexsha for p in commit.parents]
                )
                for commit in commits
            ]
        except Exception as e:
            raise GitError(f"获取提交列表失败: {str(e)}")
    
    def get_diff(
        self, 
        commit_sha: str = None,
        base_sha: str = None,
        paths: List[str] = None
    ) -> DiffInfo:
        """获取差异信息"""
        try:
            if commit_sha:
                commit = self.repo.commit(commit_sha)
                if base_sha:
                    base_commit = self.repo.commit(base_sha)
                    diff = base_commit.diff(commit)
                else:
                    # 与父提交对比
                    if commit.parents:
                        diff = commit.parents[0].diff(commit)
                    else:
                        # 初始提交，与空树对比
                        diff = commit.diff(git.NULL_TREE)
            else:
                # 工作区差异
                diff = self.repo.head.commit.diff(None)
            
            # 解析文件变更
            files = []
            total_additions = 0
            total_deletions = 0
            
            for item in diff:
                change_type = 'M'  # 默认为修改
                if item.new_file:
                    change_type = 'A'
                elif item.deleted_file:
                    change_type = 'D'
                elif item.renamed_file:
                    change_type = 'R'
                
                file_path = item.b_path or item.a_path
                old_path = item.a_path if item.renamed_file else None
                
                # 获取变更统计
                try:
                    # 尝试获取变更行数
                    if hasattr(item, 'stats') and item.stats:
                        additions = item.stats.get('insertions', 0)
                        deletions = item.stats.get('deletions', 0)
                    else:
                        additions = 0
                        deletions = 0
                except:
                    additions = 0
                    deletions = 0
                
                # 检查是否为二进制文件
                is_binary = False
                try:
                    if item.diff:
                        is_binary = b'\x00' in item.diff
                except:
                    pass
                
                files.append(FileChange(
                    file_path=file_path,
                    change_type=change_type,
                    old_path=old_path,
                    additions=additions,
                    deletions=deletions,
                    binary=is_binary
                ))
                
                total_additions += additions
                total_deletions += deletions
            
            return DiffInfo(
                commit_sha=commit_sha or 'working_tree',
                base_sha=base_sha,
                files=files,
                additions=total_additions,
                deletions=total_deletions
            )
            
        except Exception as e:
            raise GitError(f"获取差异信息失败: {str(e)}")
    
    def get_branches(self, include_remote: bool = False) -> List[BranchInfo]:
        """获取分支列表"""
        try:
            branches = []
            
            # 本地分支
            for branch in self.repo.branches:
                branches.append(BranchInfo(
                    name=branch.name,
                    commit_sha=branch.commit.hexsha,
                    is_current=branch == self.repo.active_branch,
                    is_remote=False
                ))
            
            # 远程分支
            if include_remote:
                for remote in self.repo.remotes:
                    for ref in remote.refs:
                        # 跳过HEAD引用
                        if ref.name.endswith('/HEAD'):
                            continue
                        
                        branch_name = ref.name.split('/')[-1]
                        branches.append(BranchInfo(
                            name=branch_name,
                            commit_sha=ref.commit.hexsha,
                            is_current=False,
                            is_remote=True,
                            remote_name=remote.name
                        ))
            
            return branches
            
        except Exception as e:
            raise GitError(f"获取分支列表失败: {str(e)}")
    
    def get_tags(self) -> List[TagInfo]:
        """获取标签列表"""
        try:
            tags = []
            
            for tag in self.repo.tags:
                tag_info = TagInfo(
                    name=tag.name,
                    commit_sha=tag.commit.hexsha
                )
                
                # 尝试获取标签对象信息
                try:
                    if hasattr(tag.tag, 'message'):
                        tag_info.message = tag.tag.message
                    if hasattr(tag.tag, 'tagger'):
                        tag_info.tagger_name = tag.tag.tagger.name
                        tag_info.tagger_email = tag.tag.tagger.email
                        tag_info.tagged_date = datetime.fromtimestamp(tag.tag.tagged_date)
                except:
                    pass
                
                tags.append(tag_info)
            
            return tags
            
        except Exception as e:
            raise GitError(f"获取标签列表失败: {str(e)}")
    
    def checkout_branch(self, branch_name: str, create: bool = False) -> None:
        """切换分支"""
        try:
            if create:
                # 创建并切换到新分支
                new_branch = self.repo.create_head(branch_name)
                new_branch.checkout()
            else:
                # 切换到现有分支
                self.repo.heads[branch_name].checkout()
                
        except Exception as e:
            raise GitError(f"切换分支失败: {str(e)}")
    
    def create_branch(self, branch_name: str, start_point: str = None) -> BranchInfo:
        """创建分支"""
        try:
            if start_point:
                commit = self.repo.commit(start_point)
                new_branch = self.repo.create_head(branch_name, commit)
            else:
                new_branch = self.repo.create_head(branch_name)
            
            return BranchInfo(
                name=new_branch.name,
                commit_sha=new_branch.commit.hexsha,
                is_current=False,
                is_remote=False
            )
            
        except Exception as e:
            raise GitError(f"创建分支失败: {str(e)}")
    
    def delete_branch(self, branch_name: str, force: bool = False) -> None:
        """删除分支"""
        try:
            self.repo.delete_head(branch_name, force=force)
        except Exception as e:
            raise GitError(f"删除分支失败: {str(e)}")
    
    def merge_branch(
        self, 
        source_branch: str, 
        target_branch: str = None,
        message: str = None
    ) -> MergeInfo:
        """合并分支"""
        try:
            # 切换到目标分支
            if target_branch:
                self.checkout_branch(target_branch)
            
            current_branch = self.repo.active_branch.name
            
            # 执行合并
            source = self.repo.heads[source_branch]
            merge_result = self.repo.git.merge(source.name)
            
            # 检查是否有冲突
            conflicts = []
            if self.repo.index.conflicts:
                conflicts = list(self.repo.index.conflicts.keys())
            
            merge_commit = None
            if not conflicts:
                merge_commit = self.repo.head.commit.hexsha
            
            return MergeInfo(
                source_branch=source_branch,
                target_branch=current_branch,
                merge_commit=merge_commit,
                conflicts=conflicts
            )
            
        except Exception as e:
            raise GitError(f"合并分支失败: {str(e)}")
    
    def add_files(self, files: List[str] = None) -> None:
        """添加文件到暂存区"""
        try:
            if files:
                self.repo.index.add(files)
            else:
                # 添加所有变更
                self.repo.git.add(A=True)
        except Exception as e:
            raise GitError(f"添加文件失败: {str(e)}")
    
    def commit(self, message: str, author: str = None) -> CommitInfo:
        """创建提交"""
        try:
            if not self.repo.index.diff("HEAD"):
                raise GitError("没有需要提交的变更")
            
            kwargs = {}
            if author:
                kwargs['author'] = git.Actor.from_string(author)
            
            commit = self.repo.index.commit(message, **kwargs)
            
            return self.get_commit_info(commit.hexsha)
            
        except Exception as e:
            raise GitError(f"创建提交失败: {str(e)}")
    
    def reset(self, commit_sha: str = None, mode: str = "mixed") -> None:
        """重置到指定提交"""
        try:
            if commit_sha:
                commit = self.repo.commit(commit_sha)
            else:
                commit = "HEAD"
            
            if mode == "soft":
                self.repo.head.reset(commit, index=False, working_tree=False)
            elif mode == "mixed":
                self.repo.head.reset(commit, index=True, working_tree=False)
            elif mode == "hard":
                self.repo.head.reset(commit, index=True, working_tree=True)
            else:
                raise ValueError(f"不支持的重置模式: {mode}")
                
        except Exception as e:
            raise GitError(f"重置失败: {str(e)}")
    
    def fetch(self, remote: str = "origin") -> None:
        """从远程仓库获取更新"""
        try:
            self.repo.remotes[remote].fetch()
        except Exception as e:
            raise GitError(f"获取远程更新失败: {str(e)}")
    
    def pull(self, remote: str = "origin", branch: str = None) -> None:
        """拉取远程分支"""
        try:
            if branch:
                self.repo.remotes[remote].pull(branch)
            else:
                self.repo.remotes[remote].pull()
        except Exception as e:
            raise GitError(f"拉取远程分支失败: {str(e)}")
    
    def push(self, remote: str = "origin", branch: str = None, force: bool = False) -> None:
        """推送到远程仓库"""
        try:
            if branch:
                self.repo.remotes[remote].push(branch, force=force)
            else:
                self.repo.remotes[remote].push(force=force)
        except Exception as e:
            raise GitError(f"推送失败: {str(e)}")
    
    def stash(self, message: str = None, include_untracked: bool = False) -> None:
        """创建储藏"""
        try:
            kwargs = {}
            if message:
                kwargs['message'] = message
            if include_untracked:
                kwargs['include_untracked'] = True
            
            self.repo.git.stash('push', **kwargs)
        except Exception as e:
            raise GitError(f"创建储藏失败: {str(e)}")
    
    def stash_pop(self, index: int = 0) -> None:
        """恢复储藏"""
        try:
            self.repo.git.stash('pop', f'stash@{{{index}}}')
        except Exception as e:
            raise GitError(f"恢复储藏失败: {str(e)}")
    
    def get_file_content(self, file_path: str, commit_sha: str = None) -> str:
        """获取文件内容"""
        try:
            if commit_sha:
                commit = self.repo.commit(commit_sha)
                blob = commit.tree[file_path]
                return blob.data_stream.read().decode('utf-8')
            else:
                full_path = self.repo_path / file_path
                return full_path.read_text(encoding='utf-8')
        except Exception as e:
            raise GitError(f"获取文件内容失败: {str(e)}")
    
    def get_changed_files_between_commits(
        self, 
        base_sha: str, 
        head_sha: str
    ) -> List[FileChange]:
        """获取两个提交之间的变更文件"""
        try:
            base_commit = self.repo.commit(base_sha)
            head_commit = self.repo.commit(head_sha)
            
            diff = base_commit.diff(head_commit)
            
            files = []
            for item in diff:
                change_type = 'M'
                if item.new_file:
                    change_type = 'A'
                elif item.deleted_file:
                    change_type = 'D'
                elif item.renamed_file:
                    change_type = 'R'
                
                file_path = item.b_path or item.a_path
                old_path = item.a_path if item.renamed_file else None
                
                files.append(FileChange(
                    file_path=file_path,
                    change_type=change_type,
                    old_path=old_path
                ))
            
            return files
            
        except Exception as e:
            raise GitError(f"获取变更文件失败: {str(e)}")

