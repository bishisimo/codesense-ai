"""
上下文构建器实现
"""
from typing import Dict, Any, Optional, List
from app.core.logging import get_logger
from app.services.review.ai_interfaces import ContextBuilderInterface, ContextInfo

logger = get_logger("context_builder")


class AIContextBuilder(ContextBuilderInterface):
    """AI上下文构建器"""
    
    async def build_context(self, merge_request: Any, project: Any, commit_sha: str, review_type: str) -> ContextInfo:
        """构建基础上下文信息"""
        return ContextInfo(
            project_name=project.name,
            mr_title=merge_request.title,
            source_branch=merge_request.source_branch,
            target_branch=merge_request.target_branch,
            commits_count=merge_request.commits_count or 0,
            changes_count=merge_request.changes_count or 0,
            additions_count=merge_request.additions_count or 0,
            deletions_count=merge_request.deletions_count or 0,
            commit_sha=commit_sha,
            review_type=review_type
        )
    
    async def build_enhanced_context(self, context: ContextInfo, git_service: Any) -> ContextInfo:
        """构建增强上下文信息"""
        try:
            # 获取详细的差异信息
            diff_info = git_service.get_commit_changes(context.commit_sha)
            
            # 分析代码复杂度
            complexity_analysis = git_service.analyze_code_complexity(diff_info)
            
            # 获取提交统计
            recent_commits = git_service.get_branch_commits(
                context.source_branch, limit=10
            )
            commit_stats = git_service.get_commit_statistics(recent_commits)
            
            # 构建增强信息
            enhanced_diff_info = {
                "total_files": len(diff_info.files),
                "total_changes": diff_info.total_changes,
                "file_types": self._analyze_file_types(diff_info.files),
                "large_files": self._identify_large_files(diff_info.files),
                "binary_files": self._identify_binary_files(diff_info.files)
            }
            
            # 更新上下文
            context.complexity_analysis = complexity_analysis
            context.commit_statistics = commit_stats
            context.diff_info = enhanced_diff_info
            
            logger.info(f"增强上下文构建完成: complexity={complexity_analysis.get('complexity_level', 'unknown')}")
            
        except Exception as e:
            logger.warning(f"构建增强上下文失败: {str(e)}")
            # 保持原有上下文不变
        
        return context
    
    def _analyze_file_types(self, files) -> Dict[str, int]:
        """分析文件类型分布"""
        file_types = {}
        for file_change in files:
            ext = file_change.file_path.split('.')[-1] if '.' in file_change.file_path else 'no_ext'
            file_types[ext] = file_types.get(ext, 0) + 1
        return file_types
    
    def _identify_large_files(self, files, threshold: int = 500) -> List[Dict[str, Any]]:
        """识别大文件变更"""
        large_files = []
        for file_change in files:
            if file_change.additions + file_change.deletions > threshold:
                large_files.append({
                    "path": file_change.file_path,
                    "changes": file_change.additions + file_change.deletions
                })
        return large_files
    
    def _identify_binary_files(self, files) -> List[str]:
        """识别二进制文件"""
        binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.pdf', '.zip', '.tar', '.gz', '.rar'}
        binary_files = []
        for file_change in files:
            if any(file_change.file_path.lower().endswith(ext) for ext in binary_extensions):
                binary_files.append(file_change.file_path)
        return binary_files
