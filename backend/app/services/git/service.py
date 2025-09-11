"""
Git服务 - 使用GitX封装的Git操作服务
"""
import os
from typing import List, Optional, Dict, Any
from pathlib import Path

from app.libs.gitx import GitClient, GitError, CommitInfo, DiffInfo, FileChange
from app.core.config import settings


class GitService:
    """Git操作服务"""
    
    def __init__(self, repo_path: str = None):
        """
        初始化Git服务
        
        Args:
            repo_path: Git仓库路径，如果为None则使用配置中的路径
        """
        self.repo_path = repo_path or self._get_default_repo_path()
        self._git_client = None
    
    def _get_default_repo_path(self) -> str:
        """获取默认仓库路径"""
        # 可以从配置中获取，这里先使用临时路径
        return getattr(settings, 'GIT_REPO_PATH', '/tmp/repos')
    
    @property
    def git_client(self) -> GitClient:
        """获取Git客户端"""
        if self._git_client is None:
            self._git_client = GitClient(self.repo_path)
        return self._git_client
    
    def clone_repository(self, repo_url: str, target_path: str = None) -> str:
        """
        克隆仓库
        
        Args:
            repo_url: 仓库URL
            target_path: 目标路径
            
        Returns:
            克隆后的仓库路径
        """
        if target_path is None:
            # 从URL中提取仓库名作为目标路径
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            target_path = os.path.join(self.repo_path, repo_name)
        
        try:
            # 使用GitPython的clone方法
            from git import Repo
            Repo.clone_from(repo_url, target_path)
            return target_path
        except Exception as e:
            raise GitError(f"克隆仓库失败: {str(e)}")
    
    def get_merge_request_diff(
        self, 
        source_branch: str, 
        target_branch: str = "main"
    ) -> DiffInfo:
        """
        获取合并请求的差异信息
        
        Args:
            source_branch: 源分支
            target_branch: 目标分支
            
        Returns:
            差异信息
        """
        try:
            # 切换到源分支
            self.git_client.checkout_branch(source_branch)
            
            # 获取两个分支的最新提交
            source_commit = self.git_client.get_commits(source_branch, limit=1)[0]
            target_commit = self.git_client.get_commits(target_branch, limit=1)[0]
            
            # 获取差异
            return self.git_client.get_diff(
                commit_sha=source_commit.sha,
                base_sha=target_commit.sha
            )
            
        except Exception as e:
            raise GitError(f"获取合并请求差异失败: {str(e)}")
    
    def get_commit_changes(self, commit_sha: str) -> DiffInfo:
        """
        获取指定提交的变更
        
        Args:
            commit_sha: 提交SHA
            
        Returns:
            差异信息
        """
        try:
            return self.git_client.get_diff(commit_sha=commit_sha)
        except Exception as e:
            raise GitError(f"获取提交变更失败: {str(e)}")
    
    def get_file_diff_content(
        self, 
        file_path: str, 
        source_sha: str, 
        target_sha: str = None
    ) -> str:
        """
        获取文件的差异内容
        
        Args:
            file_path: 文件路径
            source_sha: 源提交SHA
            target_sha: 目标提交SHA，如果为None则与父提交比较
            
        Returns:
            差异内容
        """
        try:
            # 获取文件在不同提交中的内容
            source_content = self.git_client.get_file_content(file_path, source_sha)
            
            if target_sha:
                target_content = self.git_client.get_file_content(file_path, target_sha)
            else:
                # 获取父提交
                commit_info = self.git_client.get_commit_info(source_sha)
                if commit_info.parents:
                    target_content = self.git_client.get_file_content(
                        file_path, commit_info.parents[0]
                    )
                else:
                    target_content = ""
            
            # 生成简单的差异（实际项目中可以使用更专业的diff库）
            return self._generate_simple_diff(target_content, source_content, file_path)
            
        except Exception as e:
            raise GitError(f"获取文件差异失败: {str(e)}")
    
    def _generate_simple_diff(
        self, 
        old_content: str, 
        new_content: str, 
        file_path: str
    ) -> str:
        """
        生成简单的差异格式
        
        Args:
            old_content: 原内容
            new_content: 新内容
            file_path: 文件路径
            
        Returns:
            差异字符串
        """
        import difflib
        
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=""
        )
        
        return ''.join(diff)
    
    def get_branch_commits(
        self, 
        branch: str, 
        limit: int = 100,
        since_commit: str = None
    ) -> List[CommitInfo]:
        """
        获取分支的提交列表
        
        Args:
            branch: 分支名
            limit: 限制数量
            since_commit: 起始提交
            
        Returns:
            提交信息列表
        """
        try:
            return self.git_client.get_commits(branch=branch, limit=limit)
        except Exception as e:
            raise GitError(f"获取分支提交失败: {str(e)}")
    
    def analyze_code_complexity(self, diff_info: DiffInfo) -> Dict[str, Any]:
        """
        分析代码复杂度
        
        Args:
            diff_info: 差异信息
            
        Returns:
            复杂度分析结果
        """
        try:
            analysis = {
                "total_files": len(diff_info.files),
                "total_lines_changed": diff_info.total_changes,
                "additions": diff_info.additions,
                "deletions": diff_info.deletions,
                "file_types": {},
                "large_files": [],
                "binary_files": []
            }
            
            # 分析文件类型
            for file_change in diff_info.files:
                if file_change.binary:
                    analysis["binary_files"].append(file_change.file_path)
                    continue
                
                # 大文件标记（变更超过100行）
                if file_change.additions + file_change.deletions > 100:
                    analysis["large_files"].append({
                        "path": file_change.file_path,
                        "changes": file_change.additions + file_change.deletions
                    })
                
                # 文件类型统计
                file_ext = Path(file_change.file_path).suffix.lower()
                if file_ext:
                    analysis["file_types"][file_ext] = analysis["file_types"].get(file_ext, 0) + 1
            
            # 计算复杂度评分（简单算法）
            complexity_score = 0
            if analysis["total_lines_changed"] > 500:
                complexity_score += 3
            elif analysis["total_lines_changed"] > 200:
                complexity_score += 2
            elif analysis["total_lines_changed"] > 50:
                complexity_score += 1
            
            if analysis["total_files"] > 20:
                complexity_score += 2
            elif analysis["total_files"] > 10:
                complexity_score += 1
            
            if len(analysis["binary_files"]) > 0:
                complexity_score += 1
            
            analysis["complexity_score"] = complexity_score
            analysis["complexity_level"] = self._get_complexity_level(complexity_score)
            
            return analysis
            
        except Exception as e:
            raise GitError(f"分析代码复杂度失败: {str(e)}")
    
    def _get_complexity_level(self, score: int) -> str:
        """获取复杂度级别"""
        if score >= 5:
            return "very_high"
        elif score >= 3:
            return "high"
        elif score >= 2:
            return "medium"
        elif score >= 1:
            return "low"
        else:
            return "very_low"
    
    def get_commit_statistics(self, commits: List[CommitInfo]) -> Dict[str, Any]:
        """
        获取提交统计信息
        
        Args:
            commits: 提交列表
            
        Returns:
            统计信息
        """
        if not commits:
            return {}
        
        # 作者统计
        authors = {}
        for commit in commits:
            author = commit.author_name
            authors[author] = authors.get(author, 0) + 1
        
        # 时间统计
        dates = [commit.authored_date.date() for commit in commits]
        date_range = {
            "earliest": min(dates),
            "latest": max(dates),
            "span_days": (max(dates) - min(dates)).days
        }
        
        return {
            "total_commits": len(commits),
            "authors": authors,
            "most_active_author": max(authors.items(), key=lambda x: x[1])[0] if authors else None,
            "date_range": date_range,
            "average_commits_per_day": len(commits) / max(date_range["span_days"], 1)
        }
    
    def validate_repository(self) -> Dict[str, Any]:
        """
        验证仓库状态
        
        Returns:
            验证结果
        """
        try:
            repo_info = self.git_client.get_repository_info()
            
            validation = {
                "is_valid": True,
                "current_branch": repo_info.current_branch,
                "has_remote": bool(repo_info.remote_url),
                "is_clean": not repo_info.is_dirty,
                "untracked_files_count": len(repo_info.untracked_files),
                "issues": []
            }
            
            # 检查问题
            if repo_info.is_dirty:
                validation["issues"].append("存在未提交的变更")
            
            if not repo_info.remote_url:
                validation["issues"].append("未配置远程仓库")
            
            if len(repo_info.untracked_files) > 0:
                validation["issues"].append(f"存在{len(repo_info.untracked_files)}个未跟踪文件")
            
            return validation
            
        except Exception as e:
            return {
                "is_valid": False,
                "error": str(e),
                "issues": [f"仓库验证失败: {str(e)}"]
            }

