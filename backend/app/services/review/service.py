"""
ReviewService - 使用新的AI审查器架构
"""
from typing import Dict, List, Optional, Any
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
import re

from app.core.config import settings
from app.models import MergeRequest, CodeReview, ReviewComment, Project, AIModel, TokenUsage
from app.libs.ai_models import get_model_definition
from app.libs.gitlabx import GitLabClient
from app.libs.gitx import GitError
from app.services.git import GitService
from app.services.review.ai_reviewer import AIReviewer
from app.services.review.ai_interfaces import ReviewRequest, ContextInfo
from app.libs.file_filter import get_file_filter
from app.core.logging import get_logger

logger = get_logger("review_service")


class ReviewService:
    """代码审查服务 - 使用新的AI审查器架构"""

    def __init__(self, repo_path: str = None):
        self._gitlab_client = None
        self._ai_reviewer = None
        self._git_service = None
        self._repo_path = repo_path
    
    @property
    def gitlab_client(self):
        """延迟初始化GitLab客户端"""
        if self._gitlab_client is None:
            self._gitlab_client = GitLabClient(
                url=settings.GITLAB_URL,
                token=settings.GITLAB_TOKEN
            )
        return self._gitlab_client
    
    @property
    def ai_reviewer(self):
        """延迟初始化AI审查器"""
        if self._ai_reviewer is None:
            self._ai_reviewer = AIReviewer()
        return self._ai_reviewer
    
    @property
    def git_service(self):
        """延迟初始化Git服务"""
        if self._git_service is None and self._repo_path:
            self._git_service = GitService(self._repo_path)
        return self._git_service

    async def review_merge_request(
            self,
            session: AsyncSession,
            merge_request: MergeRequest,
            force_refresh: bool = False,
            review_type: str = "standard",
            template_name: Optional[str] = None,
            template_id: Optional[int] = None,
            custom_instructions: str = ""
    ) -> Optional[CodeReview]:
        """审查合并请求 - 统一入口方法
        
        Args:
            session: 数据库会话
            merge_request: 合并请求对象
            force_refresh: 是否强制刷新
            review_type: 审查类型 ("standard" | "enhanced")
        """
        try:
            # 获取项目信息
            project = await session.get(Project, merge_request.project_id)
            if not project:
                raise ValueError(f"Project not found: {merge_request.project_id}")

            # 使用MR表中的最新commit sha，而不是从GitLab API获取
            if not merge_request.last_commit_sha:
                raise ValueError("MR没有最新的commit sha信息，请先同步MR数据")

            commit_sha = merge_request.last_commit_sha

            # 检查是否已经有审查中的记录
            pending_review = await session.scalar(
                select(CodeReview).where(
                    CodeReview.merge_request_id == merge_request.id,
                    CodeReview.status == "pending"
                )
            )

            if pending_review and not force_refresh:
                logger.info(f"MR {merge_request.id} 已有审查中的记录，跳过重复审查")
                return pending_review

            # 检查是否已经对此提交进行过审查
            existing_review = await session.scalar(
                select(CodeReview).where(
                    CodeReview.merge_request_id == merge_request.id,
                    CodeReview.commit_sha == commit_sha,
                    CodeReview.status == "completed"
                )
            )

            # 只有在有pending记录时才需要force参数，completed记录不影响新的审查
            if existing_review and force_refresh:
                # 删除现有审查和评论
                await session.execute(
                    delete(ReviewComment).where(ReviewComment.review_id == existing_review.id)
                )
                await session.delete(existing_review)
                await session.flush()

            # 如果有审查中的记录且强制刷新，删除它
            if pending_review and force_refresh:
                await session.execute(
                    delete(ReviewComment).where(ReviewComment.review_id == pending_review.id)
                )
                await session.delete(pending_review)
                await session.flush()

            # 创建新的审查记录
            review = CodeReview(
                merge_request_id=merge_request.id,
                commit_sha=commit_sha,
                reviewer_type="",  # 将在AI审查完成后设置实际模型名称
                status="pending"
            )
            session.add(review)
            await session.flush()

            # 先提交pending状态到数据库
            await session.commit()

            # 异步执行AI审查
            import asyncio
            asyncio.create_task(self._async_review_process(
                review.id, project.id, merge_request.id, commit_sha, review_type, template_name, template_id, custom_instructions
            ))

            logger.info(f"AI review started for MR {merge_request.id} (type: {review_type}, commit: {commit_sha})")
            return review

        except Exception as e:
            await session.rollback()

            # 更新审查状态为失败
            if 'review' in locals():
                try:
                    review.status = "failed"
                    review.error_message = str(e)
                    review.review_content = f"审查失败: {str(e)}"
                    
                    # 尝试为失败的审查创建token使用记录
                    try:
                        await self._create_failed_token_usage_record(session, review, e)
                    except Exception as token_error:
                        logger.error(f"Failed to create token usage record for failed review: {token_error}")
                    
                    await session.commit()
                except Exception as commit_error:
                    logger.error(f"Failed to update review status: {commit_error}")

            import traceback
            logger.error(f"Code review failed: {str(e)}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise e

    async def enhanced_review_merge_request(
            self,
            session: AsyncSession,
            merge_request: MergeRequest,
            repo_path: str,
            force_refresh: bool = False
    ) -> Optional[CodeReview]:
        """增强审查合并请求 - 复用标准审查方法"""
        # 确保Git服务已初始化
        if not self._repo_path:
            self._repo_path = repo_path
        
        # 验证仓库状态
        repo_validation = self.git_service.validate_repository()
        if not repo_validation["is_valid"]:
            raise ValueError(f"仓库验证失败: {repo_validation.get('error', 'Unknown error')}")

        # 复用标准审查方法，传入enhanced类型
        return await self.review_merge_request(
            session=session,
            merge_request=merge_request,
            force_refresh=force_refresh,
            review_type="enhanced"
        )

    async def _async_review_process(
            self,
            review_id: int,
            project_id: int,
            merge_request_id: int,
            commit_sha: str,
            review_type: str = "standard",
            template_name: Optional[str] = None,
            template_id: Optional[int] = None,
            custom_instructions: str = ""
    ):
        """异步执行AI审查过程"""
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as new_session:
            try:
                # 重新获取review对象
                review = await new_session.get(CodeReview, review_id)
                if not review:
                    logger.error(f"Review {review_id} not found in async process")
                    return
                
                # 重新获取project和merge_request对象
                project = await new_session.get(Project, project_id)
                merge_request = await new_session.get(MergeRequest, merge_request_id)
                
                if not project or not merge_request:
                    logger.error(f"Project {project_id} or MergeRequest {merge_request_id} not found in async process")
                    return

                # 构建AI审查上下文
                context = await self._build_ai_context(
                    new_session, project, merge_request, commit_sha, review_type
                )

                # 获取代码差异
                code_diff = await self._get_code_diff(project, merge_request, commit_sha, review_type)
                if not code_diff.strip():
                    raise ValueError("代码差异为空，无法进行审查")

                logger.info(f"Starting {review_type} AI review for MR {merge_request.id} (commit: {commit_sha})")
                logger.debug(f"Code diff length: {len(code_diff)} characters")

                # 获取指定模板或使用默认模板
                template = None
                if template_name:
                    template = await self.ai_reviewer.get_template_by_name(template_name)
                    if not template:
                        logger.warning(f"指定的模板 '{template_name}' 不存在，使用默认模板")
                
                # 创建审查请求，将自定义指令添加到context中
                if custom_instructions:
                    # 将自定义指令添加到context中，供模板渲染器使用
                    context.custom_instructions = custom_instructions

                # 创建审查请求
                review_request = ReviewRequest(
                    code_diff=code_diff,
                    context=context,
                    template=template
                )

                # 执行AI审查
                review_result = await self.ai_reviewer.review(review_request)

                # 验证审查结果
                if not review_result:
                    raise ValueError("AI审查返回空结果")

                # 处理审查结果
                await self._process_review_result(
                    new_session, review, review_result, context, review_type
                )

                logger.info(f"{review_type.capitalize()} AI review completed for MR {merge_request.id} with score {review.score}")

            except Exception as e:
                await new_session.rollback()

                # 更新审查状态为失败
                try:
                    # 重新获取review对象以确保在当前会话中
                    failed_review = await new_session.get(CodeReview, review_id)
                    if failed_review:
                        failed_review.status = "failed"
                        failed_review.error_message = str(e)
                        failed_review.review_content = f"AI审查失败: {str(e)}"
                        
                        # 尝试为失败的审查创建token使用记录
                        try:
                            await self._create_failed_token_usage_record(new_session, failed_review, e)
                        except Exception as token_error:
                            logger.error(f"Failed to create token usage record for failed review: {token_error}")
                        
                        await new_session.commit()
                        logger.info(f"Review {review_id} status updated to failed")
                    else:
                        logger.error(f"Failed to find review {review_id} for status update")
                except Exception as commit_error:
                    logger.error(f"Failed to update review status: {commit_error}")

                import traceback
                logger.error(f"Async code review failed: {str(e)}")
                logger.debug(f"Traceback: {traceback.format_exc()}")

    async def _build_ai_context(
            self,
            session: AsyncSession,
            project: Project,
            merge_request: MergeRequest,
            commit_sha: str,
            review_type: str
    ) -> ContextInfo:
        """构建AI审查上下文"""
        # 构建基础上下文
        context = await self.ai_reviewer.context_builder.build_context(
            merge_request, project, commit_sha, review_type
        )

        # 增强审查类型需要额外的上下文信息
        if review_type == "enhanced" and self.git_service:
            try:
                context = await self.ai_reviewer.context_builder.build_enhanced_context(
                    context, self.git_service
                )
                logger.info(f"Enhanced context built: complexity={context.complexity_analysis.get('complexity_level', 'unknown') if context.complexity_analysis else 'unknown'}")
            except Exception as e:
                logger.warning(f"Failed to build enhanced context: {str(e)}")
                # 降级到标准上下文

        return context

    async def _get_code_diff(
            self,
            project: Project,
            merge_request: MergeRequest,
            commit_sha: str,
            review_type: str
    ) -> str:
        """获取代码差异"""
        try:
            # 增强审查优先使用gitx
            if review_type == "enhanced" and self.git_service:
                try:
                    diff_info = self.git_service.get_commit_changes(commit_sha)
                    return self._build_diff_from_gitx(diff_info, project)
                except GitError as e:
                    logger.warning(f"GitX获取差异失败，降级到GitLab API: {str(e)}")

            # 降级到GitLab API
            changes = self.gitlab_client.get_merge_request_changes(
                project.gitlab_id, merge_request.gitlab_id
            )

            if not changes:
                raise ValueError("无法获取合并请求的代码变更")

            return self._build_diff_text(changes, project)

        except Exception as e:
            raise ValueError(f"获取代码差异失败: {str(e)}")

    async def _process_review_result(
            self,
            session: AsyncSession,
            review: CodeReview,
            review_result: Any,
            context: ContextInfo,
            review_type: str
    ):
        """处理审查结果"""
        try:
            # 基础评分
            base_score = review_result.score
            
            # 增强审查需要额外的评分处理
            if review_type == "enhanced":
                complexity_analysis = context.complexity_analysis
                if complexity_analysis:
                    enhanced_score = self._calculate_enhanced_score(base_score, complexity_analysis)
                    enhanced_score = await self._avoid_duplicate_score(session, review.merge_request_id, enhanced_score)
                    final_score = enhanced_score
                else:
                    final_score = base_score
            else:
                final_score = base_score

            # 更新审查结果
            review.score = final_score
            review.score_details = review_result.score_details
            review.review_content = self._build_review_markdown(
                review_result, 
                context.complexity_analysis,
                context.commit_statistics
            )
            review.code_suggestion = self._build_code_suggestions(review_result)
            
            # 设置错误信息（如果有）
            if hasattr(review_result, 'error_message') and review_result.error_message:
                review.error_message = review_result.error_message
            
            # 设置实际使用的模型名称
            if hasattr(review_result, 'model_used') and review_result.model_used:
                review.reviewer_type = review_result.model_used
            else:
                # 如果没有模型信息，使用默认配置
                default_config = self.ai_reviewer.get_default_model_config()
                review.reviewer_type = f"{default_config.provider.value}/{default_config.model_name}"
            
            # 根据分数判断审查状态：分数为0表示审查失败
            if final_score == 0:
                review.status = "failed"
                review.error_message = "审查失败：评分为0"
                logger.warning(f"Review failed for MR {review.merge_request_id} due to score 0")
            else:
                review.status = "completed"
            
            # 创建TokenUsage记录
            try:
                await self._create_token_usage_record(session, review, review_result)
            except Exception as e:
                logger.error(f"Failed to create token usage record: {str(e)}")

            # 创建审查评论
            try:
                await self._create_review_comments(session, review, review_result)
            except Exception as e:
                logger.error(f"Failed to create review comments: {str(e)}")

            await session.commit()

            # 发送通知
            try:
                merge_request = await session.get(MergeRequest, review.merge_request_id)
                if merge_request:
                    project = await session.get(Project, merge_request.project_id)
                    await self._send_notifications(merge_request, review, project)
                else:
                    logger.error(f"Merge request not found for review {review.id}")
            except Exception as e:
                logger.error(f"Failed to send notifications: {str(e)}")
                
        except Exception as e:
            # 如果处理审查结果时出现异常，将状态设置为失败
            logger.error(f"Failed to process review result: {str(e)}")
            review.status = "failed"
            review.error_message = str(e)
            review.review_content = f"处理审查结果失败: {str(e)}"
            
            # 尝试为失败的审查创建token使用记录
            try:
                await self._create_failed_token_usage_record(session, review, e)
            except Exception as token_error:
                logger.error(f"Failed to create token usage record for failed review result: {token_error}")
            
            try:
                await session.commit()
            except Exception as commit_error:
                logger.error(f"Failed to commit failed status: {commit_error}")
            raise  # 重新抛出异常，让上层方法处理
    
    def _build_code_suggestions(self, review_result: Any) -> str:
        """构建代码修改建议"""
        try:
            suggestions = []
            
            # 从issues中提取建议
            if hasattr(review_result, 'issues') and review_result.issues:
                for issue in review_result.issues:
                    if isinstance(issue, dict) and issue.get('suggestion'):
                        file_info = f"**文件**: {issue.get('file', '未知文件')}"
                        if issue.get('line'):
                            file_info += f" (第{issue['line']}行)"
                        
                        suggestion_text = f"""
## {issue.get('title', '代码建议')}

{file_info}

**问题描述**: {issue.get('description', '')}

**修改建议**: {issue.get('suggestion', '')}

**严重程度**: {issue.get('severity', 'medium')}
"""
                        suggestions.append(suggestion_text)
            
            # 从improvements中提取建议（向后兼容）
            if hasattr(review_result, 'improvements') and review_result.improvements:
                for improvement in review_result.improvements:
                    if improvement:
                        suggestions.append(f"- {improvement}")
            
            if suggestions:
                return "\n\n".join(suggestions)
            else:
                return "暂无具体的代码修改建议"
                
        except Exception as e:
            logger.error(f"构建代码建议失败: {str(e)}")
            return f"构建代码建议失败: {str(e)}"

    def _calculate_enhanced_score(self, base_score: int, complexity_analysis: Dict[str, Any]) -> int:
        """根据复杂度分析计算增强评分"""
        import random

        enhanced_score = base_score

        # 根据复杂度调整评分
        complexity_level = complexity_analysis.get("complexity_level", "medium")
        if complexity_level == "very_high":
            enhanced_score -= random.randint(8, 12)
        elif complexity_level == "high":
            enhanced_score -= random.randint(3, 7)
        elif complexity_level == "very_low":
            enhanced_score += random.randint(3, 7)

        # 根据变更规模调整
        total_changes = complexity_analysis.get("total_lines_changed", 0)
        if total_changes > 1000:
            enhanced_score -= random.randint(3, 7)
        elif total_changes < 50:
            enhanced_score += random.randint(2, 5)

        # 二进制文件惩罚
        if complexity_analysis.get("binary_files"):
            enhanced_score -= random.randint(1, 3)

        # 添加微小的随机性，避免评分过于一致
        random_adjustment = random.randint(-2, 2)
        enhanced_score += random_adjustment

        # 确保评分在合理范围内
        return max(0, min(100, enhanced_score))

    async def _avoid_duplicate_score(self, session: AsyncSession, merge_request_id: int, score: int) -> int:
        """避免重复评分，如果发现相同评分则进行微调"""
        import random

        # 查询该MR的历史评分
        result = await session.execute(
            select(CodeReview.score)
            .where(
                CodeReview.merge_request_id == merge_request_id,
                CodeReview.score.isnot(None)
            )
        )

        existing_scores = [row[0] for row in result.fetchall()]

        # 如果发现相同评分，进行微调
        if score in existing_scores:
            # 在±3分范围内随机调整，但避免与现有评分重复
            for _ in range(10):  # 最多尝试10次
                adjustment = random.randint(-3, 3)
                new_score = score + adjustment
                if new_score not in existing_scores and 0 <= new_score <= 100:
                    logger.info(f"检测到重复评分 {score}，调整为 {new_score}")
                    return new_score

            # 如果无法避免重复，至少确保不完全相同
            adjustment = random.choice([-1, 1])
            new_score = max(0, min(100, score + adjustment))
            logger.info(f"无法避免重复评分，进行最小调整: {score} -> {new_score}")
            return new_score

        return score

    def _build_review_markdown(
            self,
            review_result: Any,
            complexity_analysis: Dict[str, Any] = None,
            commit_stats: Dict[str, Any] = None
    ) -> str:
        """构建Markdown格式的审查报告"""
        title = "代码审查报告"

        markdown_parts = [
            f"# {title}",
            f"",
            f"**评分**: {review_result.score}",
            f"",
        ]

        # 添加审查级别（新格式）
        if hasattr(review_result, 'level') and review_result.level:
            markdown_parts.extend([
                f"**审查级别**: {review_result.level}",
                f"",
            ])

        # 添加审查总结（新格式）
        if hasattr(review_result, 'summary') and review_result.summary:
            markdown_parts.extend([
                f"**审查总结**: {review_result.summary}",
                f"",
            ])

        # 添加详细评分
        score_details = None
        if hasattr(review_result, 'categories') and review_result.categories:
            # 新格式：从categories构建score_details
            score_details = {}
            for category in review_result.categories:
                if category.get('name') == '代码质量':
                    score_details['code_quality'] = {
                        'score': category.get('score', 0),
                        'reason': category.get('description', '')
                    }
                elif category.get('name') == '功能正确性':
                    score_details['correctness'] = {
                        'score': category.get('score', 0),
                        'reason': category.get('description', '')
                    }
                elif category.get('name') == '性能优化':
                    score_details['performance'] = {
                        'score': category.get('score', 0),
                        'reason': category.get('description', '')
                    }
                elif category.get('name') == '安全性':
                    score_details['security'] = {
                        'score': category.get('score', 0),
                        'reason': category.get('description', '')
                    }
                elif category.get('name') == '测试覆盖':
                    score_details['testing'] = {
                        'score': category.get('score', 0),
                        'reason': category.get('description', '')
                    }
        else:
            # 旧格式：直接使用score_details
            score_details = getattr(review_result, 'score_details', {})

        if score_details:
            markdown_parts.extend([
                "## 📈 详细评分",
                "",
                "| 评分维度 | 得分 | 比重 | 评分原因 |",
                "|:--------|:----:|:----:|:--------|",
            ])

            # 定义维度权重
            weights = {
                "code_quality": {"name": "代码质量", "weight": 30},
                "correctness": {"name": "功能正确性", "weight": 25},
                "performance": {"name": "性能优化", "weight": 20},
                "security": {"name": "安全性", "weight": 15},
                "testing": {"name": "测试覆盖", "weight": 10}
            }

            for dimension, config in weights.items():
                detail = score_details.get(dimension, {})
                if isinstance(detail, dict):
                    score = detail.get("score", 0)
                    reason = detail.get("reason", "未提供评分原因")
                else:
                    score = detail if detail else 0
                    reason = "未提供评分原因"

                markdown_parts.append(
                    f"| {config['name']} | {score} | {config['weight']}% | {reason} |"
                )

            markdown_parts.append("")

        # 添加问题列表（新格式）
        if hasattr(review_result, 'issues') and review_result.issues:
            # 按严重程度分组问题
            issues_by_severity = {
                'critical': [],
                'high': [],
                'medium': [],
                'low': []
            }
            
            for issue in review_result.issues:
                severity = issue.get('severity', 'medium')
                if severity in issues_by_severity:
                    issues_by_severity[severity].append(issue)
                else:
                    issues_by_severity['medium'].append(issue)
            
            markdown_parts.extend([
                "## 🔍 发现的问题",
                "",
            ])
            
            # 按严重程度顺序显示问题
            severity_order = ['critical', 'high', 'medium', 'low']
            severity_icons = {
                'critical': '🔴',
                'high': '🟠', 
                'medium': '🟡',
                'low': '🟢'
            }
            severity_names = {
                'critical': '严重问题',
                'high': '重要问题',
                'medium': '一般问题',
                'low': '轻微问题'
            }
            
            for severity in severity_order:
                issues = issues_by_severity[severity]
                if not issues:
                    continue
                
                icon = severity_icons[severity]
                name = severity_names[severity]
                
                markdown_parts.extend([
                    f"### {icon} {name}",
                    "",
                ])
                
                for issue in issues:
                    issue_type = issue.get('type', 'info')
                    category = issue.get('category', '')
                    title = issue.get('title', '')
                    description = issue.get('description', '')
                    file_path = issue.get('file', '')
                    line_number = issue.get('line')
                    suggestion = issue.get('suggestion', '')
                    
                    # 根据问题类型选择图标
                    type_icons = {
                        'error': '❌',
                        'warning': '⚠️',
                        'suggestion': '💡',
                        'info': 'ℹ️'
                    }
                    type_icon = type_icons.get(issue_type, '📝')
                    
                    # 构建问题描述
                    issue_text = f"#### {type_icon} {title}"
                    
                    # 添加元信息（使用更美观的格式）
                    meta_parts = []
                    if category:
                        meta_parts.append(f"🏷️ **{category}**")
                    if file_path:
                        file_display = f"📁 `{file_path}`"
                        if line_number:
                            file_display += f":`{line_number}`"
                        meta_parts.append(file_display)
                    if issue_type != 'info':
                        type_names = {
                            'error': '错误',
                            'warning': '警告', 
                            'suggestion': '建议',
                            'info': '信息'
                        }
                        meta_parts.append(f"🔖 {type_names.get(issue_type, issue_type)}")
                    
                    if meta_parts:
                        issue_text += f"\n\n> {' • '.join(meta_parts)}"
                    
                    # 添加问题描述（使用引用格式）
                    issue_text += f"\n\n**问题描述**:\n{description}"
                    
                    # 添加建议（使用更突出的格式）
                    if suggestion:
                        issue_text += f"\n\n**💡 改进建议**:\n{suggestion}"
                    
                    markdown_parts.append(issue_text)
                    markdown_parts.append("---")

        # 添加复杂度分析（如果有）
        if complexity_analysis:
            markdown_parts.extend([
                "## 🔍 复杂度分析",
                "",
                f"**复杂度等级**: {complexity_analysis.get('complexity_level', 'unknown')}",
                f"**总变更行数**: {complexity_analysis.get('total_lines_changed', 0)}",
                f"**新增行数**: {complexity_analysis.get('additions', 0)}",
                f"**删除行数**: {complexity_analysis.get('deletions', 0)}",
                "",
            ])

        # 添加提交统计（如果有）
        if commit_stats:
            markdown_parts.extend([
                "## 📊 提交统计",
                "",
                f"**总提交数**: {commit_stats.get('total_commits', 0)}",
                f"**主要贡献者**: {commit_stats.get('most_active_author', 'unknown')}",
                f"**时间跨度**: {commit_stats.get('date_range', {}).get('span_days', 0)} 天",
                "",
            ])

        return "\n".join(markdown_parts)

    def _build_diff_from_gitx(self, diff_info, project: Project) -> str:
        """从gitx的DiffInfo构建代码差异文本"""
        # 获取文件过滤器
        file_filter = self._get_file_filter_for_project(project)
        
        # 获取所有文件路径
        all_file_paths = [file_change.file_path for file_change in diff_info.files]
        
        # 过滤文件
        filtered_files = file_filter.filter_file_list(all_file_paths)
        ignored_files = file_filter.get_ignored_files(all_file_paths)
        
        # 记录过滤信息
        if ignored_files:
            logger.info(f"过滤了 {len(ignored_files)} 个文件，保留 {len(filtered_files)} 个文件进行审查")
            logger.debug(f"被过滤的文件: {ignored_files[:5]}{'...' if len(ignored_files) > 5 else ''}")
        
        diff_parts = []

        for file_change in diff_info.files:
            try:
                file_path = file_change.file_path
                
                # 跳过被过滤的文件
                if file_path not in filtered_files:
                    continue
                
                diff_parts.append(f"--- a/{file_path}")
                diff_parts.append(f"+++ b/{file_path}")

                # 添加变更类型信息
                if file_change.change_type == 'A':
                    diff_parts.append("@@ -0,0 +1,1 @@")
                    diff_parts.append(f"+++ 新文件: {file_path}")
                elif file_change.change_type == 'D':
                    diff_parts.append("@@ -1,1 +0,0 @@")
                    diff_parts.append(f"--- 删除文件: {file_path}")
                elif file_change.change_type == 'R':
                    diff_parts.append(f"@@ 重命名: {file_change.old_path} -> {file_path}")
                else:
                    # 修改文件，尝试获取具体差异
                    if self.git_service:
                        try:
                            file_diff = self.git_service.get_file_diff_content(
                                file_path,
                                diff_info.commit_sha,
                                diff_info.base_sha
                            )
                            diff_parts.append(file_diff)
                        except Exception:
                            diff_parts.append(f"@@ 修改文件: {file_path} (+{file_change.additions}/-{file_change.deletions})")
                    else:
                        diff_parts.append(f"@@ 修改文件: {file_path} (+{file_change.additions}/-{file_change.deletions})")

                diff_parts.append("")  # 空行分隔

            except Exception as e:
                logger.error(f"Error processing file change {file_change.file_path}: {str(e)}")
                continue

        return "\n".join(diff_parts)

    def _build_diff_text(self, changes: List[Any], project: Project) -> str:
        """构建代码差异文本"""
        # 获取文件过滤器
        file_filter = self._get_file_filter_for_project(project)
        
        # 获取所有文件路径
        all_file_paths = []
        for change in changes:
            file_path = change.new_path or change.old_path or "unknown"
            all_file_paths.append(file_path)
        
        # 过滤文件
        filtered_files = file_filter.filter_file_list(all_file_paths)
        ignored_files = file_filter.get_ignored_files(all_file_paths)
        
        # 记录过滤信息
        if ignored_files:
            logger.info(f"过滤了 {len(ignored_files)} 个文件，保留 {len(filtered_files)} 个文件进行审查")
            logger.debug(f"被过滤的文件: {ignored_files[:5]}{'...' if len(ignored_files) > 5 else ''}")
        
        diff_parts = []

        for change in changes:
            try:
                file_path = change.new_path or change.old_path or "unknown"
                
                # 跳过被过滤的文件
                if file_path not in filtered_files:
                    continue
                
                diff_parts.append(f"--- a/{file_path}")
                diff_parts.append(f"+++ b/{file_path}")

                # 确保diff不为空
                if hasattr(change, 'diff') and change.diff:
                    diff_parts.append(change.diff)
                else:
                    diff_parts.append("# No diff content available")

                diff_parts.append("")  # 空行分隔
            except Exception as e:
                logger.error(f"Error processing change: {str(e)}")
                continue

        return "\n".join(diff_parts)

    def _get_file_filter_for_project(self, project: Project):
        """
        获取项目文件过滤器
        
        Args:
            project: 项目对象
            
        Returns:
            文件过滤器实例
        """
        try:
            # 简化逻辑：只使用通用过滤器和Go语言过滤器
            # 可以根据需要在这里添加简单的判断逻辑
            # 目前默认使用通用过滤器
            return get_file_filter("default")
                
        except Exception as e:
            logger.warning(f"获取项目文件过滤器失败，使用默认过滤器: {str(e)}")
            return get_file_filter("default")
    
    def _get_go_file_filter(self):
        """
        获取Go语言文件过滤器
        
        Returns:
            Go语言文件过滤器实例
        """
        try:
            return get_file_filter("go")
        except Exception as e:
            logger.warning(f"获取Go文件过滤器失败，使用默认过滤器: {str(e)}")
            return get_file_filter("default")
    
    async def _create_token_usage_record(
            self,
            session: AsyncSession,
            review: CodeReview,
            review_result: Any
    ):
        """创建Token使用记录"""
        try:
            # 根据reviewer_type获取模型定义，然后查找对应的AI模型
            model_def = get_model_definition(review.reviewer_type)
            if not model_def:
                logger.warning(f"未找到模型定义 {review.reviewer_type}，使用默认模型")
                model_def = get_model_definition('deepseek-v3.1')  # 使用默认模型
            
            # 根据模型名称查找数据库中的模型
            if model_def:
                # 优先查找活跃的模型，如果有多个则取第一个
                result = await session.execute(
                    select(AIModel).where(
                        AIModel.model_name == model_def.name,
                        AIModel.is_active == True
                    ).order_by(AIModel.id)
                )
                ai_model = result.scalar_one_or_none()
                
                # 如果没找到活跃的，查找所有模型
                if not ai_model:
                    result = await session.execute(
                        select(AIModel).where(AIModel.model_name == model_def.name).order_by(AIModel.id)
                    )
                    ai_model = result.scalar_one_or_none()
            else:
                ai_model = None
            
            if not ai_model:
                # 如果找不到对应的模型，使用默认模型（ID=1，DeepSeek v3.1）
                logger.warning(f"未找到模型 {review.reviewer_type}，使用默认模型")
                result = await session.execute(
                    select(AIModel).where(AIModel.id == 1)  # 固定使用DeepSeek v3.1作为默认模型
                )
                ai_model = result.scalar_one_or_none()
                
                if not ai_model:
                    logger.error("未找到默认AI模型（ID=1），跳过Token使用记录")
                    return
            
            # 计算成本（如果有定价信息）
            cost = None
            if ai_model.pricing and review_result.tokens_used > 0:
                # 使用新的定价结构计算成本
                pricing_info = ai_model.pricing
                
                # 直接调用成本
                direct_input_cost = 0
                if review_result.direct_token and review_result.direct_token > 0:
                    direct_input_cost = (review_result.direct_token / 1000000) * pricing_info.get("input_cost_per_1m", 0)
                
                # 缓存调用成本
                cache_input_cost = 0
                if review_result.cache_token and review_result.cache_token > 0:
                    cached_input_price = pricing_info.get("cached_input_cost_per_1m", pricing_info.get("input_cost_per_1m", 0))
                    cache_input_cost = (review_result.cache_token / 1000000) * cached_input_price
                
                # 输出成本
                output_cost = 0
                if review_result.completion_token and review_result.completion_token > 0:
                    output_cost = (review_result.completion_token / 1000000) * pricing_info.get("output_cost_per_1m", 0)
                
                cost = direct_input_cost + cache_input_cost + output_cost
            
            # 创建TokenUsage记录
            token_usage = TokenUsage(
                model_id=ai_model.id,
                review_id=review.id,
                usage_type="review",
                total_tokens=review_result.tokens_used or 0,
                prompt_tokens=review_result.prompt_token or 0,
                completion_tokens=review_result.completion_token or 0,
                direct_tokens=review_result.direct_token or 0,
                cache_tokens=review_result.cache_token or 0,
                cost=cost,
                request_duration=review_result.request_duration
            )
            
            session.add(token_usage)
            logger.info(f"创建Token使用记录: 模型={ai_model.provider}/{ai_model.model_name}, "
                       f"总token={token_usage.total_tokens}, 成本=¥{cost or 0:.4f}")
            
        except Exception as e:
            logger.error(f"创建Token使用记录失败: {str(e)}")
            raise

    async def _create_failed_token_usage_record(
            self,
            session: AsyncSession,
            review: CodeReview,
            error: Exception
    ):
        """为失败的审查创建token使用记录"""
        try:
            # 尝试从错误信息中提取token数据
            token_data = self._extract_token_from_error(error)
            
            # 查找对应的AI模型
            ai_model = await self._find_ai_model_by_reviewer_type(session, review.reviewer_type)
            if not ai_model:
                # 如果没有找到模型，尝试使用默认模型
                try:
                    from app.services.ai.ai_service import ai_service
                    default_config = ai_service.get_model_config()
                    ai_model = await self._find_ai_model_by_name(session, default_config.provider.value, default_config.model_name)
                except Exception as e:
                    logger.warning(f"无法找到默认模型: {str(e)}")
            
            if ai_model:
                # 创建TokenUsage记录，即使token为0也要记录
                token_usage = TokenUsage(
                    model_id=ai_model.id,
                    review_id=review.id,
                    usage_type="review",
                    total_tokens=token_data.get("tokens_used", 0),
                    prompt_tokens=token_data.get("prompt_token", 0),
                    completion_tokens=token_data.get("completion_token", 0),
                    direct_tokens=token_data.get("direct_token", 0),
                    cache_tokens=token_data.get("cache_token", 0),
                    cost=0,  # 失败时成本为0
                    request_duration=token_data.get("request_duration", None)
                )
                
                session.add(token_usage)
                logger.info(f"为失败的审查创建了Token使用记录: 模型={ai_model.provider}/{ai_model.model_name}, "
                           f"总token={token_usage.total_tokens}")
            else:
                logger.warning(f"无法为失败的审查创建token记录，未找到对应的AI模型: {review.reviewer_type}")
                
        except Exception as e:
            logger.error(f"创建失败审查的token记录时出错: {str(e)}")
            # 不抛出异常，避免影响主流程

    def _extract_token_from_error(self, error: Exception) -> Dict[str, int]:
        """从错误中提取token信息"""
        token_data = {
            "tokens_used": 0,
            "prompt_token": 0,
            "completion_token": 0,
            "direct_token": 0,
            "cache_token": 0
        }
        
        try:
            # 尝试从错误信息中提取token数据
            error_str = str(error)
            
            # 如果错误信息中包含token相关信息，尝试提取
            # 这里可以根据实际的错误格式进行调整
            if "tokens_used" in error_str or "token" in error_str.lower():
                # 简单的正则表达式提取（可以根据实际情况调整）
                import re
                
                # 提取总token数
                total_match = re.search(r'tokens_used[:\s]*(\d+)', error_str, re.IGNORECASE)
                if total_match:
                    token_data["tokens_used"] = int(total_match.group(1))
                
                # 提取prompt token数
                prompt_match = re.search(r'prompt_token[:\s]*(\d+)', error_str, re.IGNORECASE)
                if prompt_match:
                    token_data["prompt_token"] = int(prompt_match.group(1))
                
                # 提取completion token数
                completion_match = re.search(r'completion_token[:\s]*(\d+)', error_str, re.IGNORECASE)
                if completion_match:
                    token_data["completion_token"] = int(completion_match.group(1))
                
                # 提取direct token数
                direct_match = re.search(r'direct_token[:\s]*(\d+)', error_str, re.IGNORECASE)
                if direct_match:
                    token_data["direct_token"] = int(direct_match.group(1))
                
                # 提取cache token数
                cache_match = re.search(r'cache_token[:\s]*(\d+)', error_str, re.IGNORECASE)
                if cache_match:
                    token_data["cache_token"] = int(cache_match.group(1))
                    
        except Exception as e:
            logger.debug(f"从错误中提取token信息失败: {str(e)}")
        
        return token_data

    async def _find_ai_model_by_reviewer_type(self, session: AsyncSession, reviewer_type: str):
        """根据reviewer_type查找AI模型"""
        try:
            if not reviewer_type:
                return None
                
            # reviewer_type格式通常是 "provider/model_name"
            if "/" in reviewer_type:
                provider, model_name = reviewer_type.split("/", 1)
            else:
                # 如果没有分隔符，尝试直接匹配模型名称
                provider = None
                model_name = reviewer_type
            
            return await self._find_ai_model_by_name(session, provider, model_name)
            
        except Exception as e:
            logger.error(f"根据reviewer_type查找AI模型失败: {str(e)}")
            return None

    async def _find_ai_model_by_name(self, session: AsyncSession, provider: str, model_name: str):
        """根据provider和model_name查找AI模型"""
        try:
            from app.models.ai_model import AIModel
            
            # 构建查询条件
            conditions = []
            if provider:
                conditions.append(AIModel.provider == provider)
            if model_name:
                conditions.append(AIModel.model_name == model_name)
            
            if not conditions:
                return None
            
            stmt = select(AIModel).where(*conditions).order_by(AIModel.id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"根据名称查找AI模型失败: {str(e)}")
            return None

    async def _create_review_comments(
            self,
            session: AsyncSession,
            review: CodeReview,
            review_result: Any
    ):
        """创建审查评论"""
        issues = review_result.issues

        for issue in issues:
            try:
                # 处理行号，确保是有效的整数
                line_number = self._parse_line_number(issue.get('line'))

                # 获取评论内容 - 优先使用 description，如果没有则使用 title，最后使用 message（向后兼容）
                content = issue.get('description', '') or issue.get('title', '') or issue.get('message', '')
                
                # 如果内容为空，跳过这个评论
                if not content or content.strip() == '':
                    logger.warning(f"Skipping comment with empty content: {issue}")
                    continue

                # 调试日志
                logger.debug(f"Creating comment: file={issue.get('file')}, line={issue.get('line')} -> {line_number}, type={issue.get('type', 'info')}, content_length={len(content)}")

                comment = ReviewComment(
                    review_id=review.id,
                    file_path=issue.get('file'),
                    line_number=line_number,
                    comment_type=issue.get('type', 'info'),
                    content=content
                )
                session.add(comment)
            except Exception as e:
                logger.error(f"Failed to create review comment: {str(e)}")
                logger.debug(f"Issue data: {issue}")
                continue

    def _parse_line_number(self, line_value) -> Optional[int]:
        """解析行号，确保返回有效的整数或None"""
        if line_value is None:
            return None

        # 如果已经是整数，直接返回
        if isinstance(line_value, int):
            return line_value if line_value > 0 else None

        # 如果是字符串，尝试转换
        if isinstance(line_value, str):
            line_value = line_value.strip()

            # 处理特殊情况
            if not line_value or line_value.lower() in ['多个', 'multiple', 'n/a', 'null', 'none', '无']:
                return None

            # 尝试提取数字
            numbers = re.findall(r'\d+', line_value)
            if numbers:
                try:
                    return int(numbers[0])
                except ValueError:
                    return None

        return None

    async def _send_notifications(
            self,
            merge_request: MergeRequest,
            review: CodeReview,
            project: Project
    ):
        """发送通知"""
        try:
            # GitLab评论通知
            if settings.NOTIFICATIONS_GITLAB_COMMENT_ENABLED:
                await self._send_gitlab_comment(merge_request, review, project)

            # 其他通知方式...

        except Exception as e:
            # 通知失败不应影响主流程
            logger.error(f"Failed to send notifications: {str(e)}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")

    async def _send_gitlab_comment(
            self,
            merge_request: MergeRequest,
            review: CodeReview,
            project: Project
    ):
        """发送GitLab评论"""
        if not review.review_content:
            return

        # 构建评论内容
        score_emoji = "🟢" if review.score >= settings.REVIEW_SCORE_EXCELLENT else \
            "🟡" if review.score >= settings.REVIEW_SCORE_GOOD else "🔴"

        comment_body = f"""
{score_emoji} **AI代码审查完成** - 评分: {review.score}

{review.review_content}

---
*From CodeSense-AI*
"""

        try:
            self.gitlab_client.create_merge_request_note(
                project.gitlab_id,
                merge_request.gitlab_id,
                comment_body
            )
        except Exception as e:
            logger.error(f"Failed to create GitLab comment: {str(e)}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")