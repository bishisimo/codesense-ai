"""
GitLab数据同步服务
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models import Project, MergeRequest, CodeReview
from app.libs.gitlabx import GitLabClient, GitLabError
from app.libs.gitlabx.models import ProjectInfo, MergeRequestInfo
from app.core.config import settings
from app.core.logging import get_logger, log_performance, LogContext

logger = get_logger("sync_service")


class SyncService:
    """GitLab数据同步服务 - 重构版本"""
    
    def __init__(self):
        self._gitlab_client = None
    
    @property
    def gitlab_client(self):
        """延迟初始化GitLab客户端"""
        if self._gitlab_client is None:
            self._gitlab_client = GitLabClient(
                url=settings.GITLAB_URL,
                token=settings.GITLAB_TOKEN
            )
        return self._gitlab_client
    
    @log_performance("sync_all_data")
    async def sync_all_data(self, session: AsyncSession) -> Dict[str, Any]:
        """同步所有数据 - 统一入口，支持智能策略选择"""
        try:
            # 检查是否需要全量同步
            sync_strategy = await self._determine_sync_strategy(session)
            
            if sync_strategy["type"] == "full":
                logger.info("type: sync strategy: full")
                return await self._full_sync(session)
            else:
                logger.info("type: sync strategy: incremental")
                return await self._incremental_sync(session, sync_strategy)
                
        except Exception as e:
            await session.rollback()
            logger.error(f"同步失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"同步失败: {str(e)}",
                "strategy": "unknown"
            }
    
    @log_performance("sync_projects")
    async def sync_projects(self, session: AsyncSession) -> Dict[str, Any]:
        """同步项目列表"""
        projects_synced = 0
        projects_updated = 0
        
        try:
            # 分页获取所有项目
            page = 1
            per_page = 100
            
            while True:
                try:
                    projects, pagination = self.gitlab_client.get_projects(page=page, per_page=per_page)
                    
                    if not projects:
                        logger.debug(f"No projects found on page {page}")
                        break
                    
                    logger.info(f"Found {len(projects)} projects on page {page}")
                    
                    for project_info in projects:
                        try:
                            result = await self._sync_project(session, project_info)
                            if result == "created":
                                projects_synced += 1
                                logger.info(f"type: project action: created name: {project_info.name}")
                            elif result == "updated":
                                projects_updated += 1
                                logger.info(f"type: project action: updated name: {project_info.name}")
                        except Exception as e:
                            logger.error(f"type: project action: sync name: {project_info.name} error: {e}")
                            continue
                    
                    if not pagination.has_next:
                        logger.debug(f"Reached last page")
                        break
                    
                    page += 1
                    
                except Exception as e:
                    logger.error(f"type: projects action: sync_page page: {page} error: {e}")
                    break
            
            total = projects_synced + projects_updated
            logger.info(f"Projects sync completed: {projects_synced} created, {projects_updated} updated, {total} total")
            
            return {
                "synced": projects_synced,
                "updated": projects_updated,
                "total": total
            }
            
        except Exception as e:
            await session.rollback()
            logger.error(f"type: sync error: {e}")
            return {
                "synced": 0,
                "updated": 0,
                "total": 0
            }
    
    @log_performance("sync_merge_requests")
    async def sync_merge_requests(self, session: AsyncSession) -> Dict[str, Any]:
        """同步合并请求"""
        mrs_synced = 0
        mrs_updated = 0
        
        try:
            # 获取所有项目
            result = await session.execute(select(Project))
            projects = result.scalars().all()
            
            for project in projects:
                try:
                    project_result = await self._sync_project_merge_requests(session, project)
                    mrs_synced += project_result["synced"]
                    mrs_updated += project_result["updated"]
                except Exception as e:
                    logger.error(f"project: {project.name} action: sync_mrs error: {e}")
                    continue
            
            total = mrs_synced + mrs_updated
            logger.info(f"type: mrs state: sync_completed synced: {mrs_synced} updated: {mrs_updated} total: {total}")
            
            return {
                "synced": mrs_synced,
                "updated": mrs_updated,
                "total": total
            }
            
        except Exception as e:
            await session.rollback()
            logger.error(f"type: mrs state: sync_failed error: {e}")
            return {
                "synced": 0,
                "updated": 0,
                "total": 0
            }
    
    async def sync_merge_request(self, session: AsyncSession, mr_gitlab_id: int, project_gitlab_id: int) -> Dict[str, Any]:
        """同步指定的合并请求（通过GitLab ID）"""
        try:
            # 查找项目
            result = await session.execute(
                select(Project).where(Project.gitlab_id == project_gitlab_id)
            )
            project = result.scalar_one_or_none()
            
            if not project:
                return {
                    "success": False,
                    "message": f"项目 {project_gitlab_id} 不存在"
                }
            
            # 查找合并请求
            result = await session.execute(
                select(MergeRequest).where(
                    MergeRequest.gitlab_id == mr_gitlab_id,
                    MergeRequest.project_id == project.id
                )
            )
            mr = result.scalar_one_or_none()
            
            if not mr:
                return {
                    "success": False,
                    "message": f"合并请求 {mr_gitlab_id} 不存在"
                }
            
            # 执行同步
            return await self.sync_single_merge_request(session, project, mr)
            
        except Exception as e:
            logger.error(f"同步合并请求失败: {str(e)}")
            return {
                "success": False,
                "message": f"同步失败: {str(e)}"
            }
    
    async def sync_project(self, session: AsyncSession, project_gitlab_id: int) -> Dict[str, Any]:
        """同步指定的项目（通过GitLab ID）"""
        try:
            # 查找项目
            result = await session.execute(
                select(Project).where(Project.gitlab_id == project_gitlab_id)
            )
            project = result.scalar_one_or_none()
            
            if not project:
                return {
                    "success": False,
                    "message": f"项目 {project_gitlab_id} 不存在"
                }
            
            # 执行项目同步
            return await self._sync_project_merge_requests(session, project)
            
        except Exception as e:
            logger.error(f"同步项目失败: {str(e)}")
            return {
                "success": False,
                "message": f"同步失败: {str(e)}"
            }

    async def sync_single_merge_request(self, session: AsyncSession, project: Project, mr: MergeRequest) -> Dict[str, Any]:
        """同步单个合并请求的最新数据"""
        try:
            # 重新查询MR对象以确保获取最新数据
            result = await session.execute(
                select(MergeRequest).where(MergeRequest.id == mr.id)
            )
            current_mr = result.scalar_one_or_none()
            
            if not current_mr:
                return {
                    "success": False,
                    "message": "合并请求不存在",
                    "details": {}
                }
            
            # 获取MR的最新信息
            mr_info = self.gitlab_client.get_merge_request(project.gitlab_id, current_mr.gitlab_id)
            
            # 获取详细的变更统计信息
            changes_stats = self.gitlab_client.get_merge_request_changes_stats(project.gitlab_id, current_mr.gitlab_id)
            
            # 获取提交列表来计算准确的提交数量
            commits = self.gitlab_client.get_merge_request_commits(project.gitlab_id, current_mr.gitlab_id)
            commits_count = len(commits) if commits else 0
            
            # 更新MR信息
            current_mr.title = mr_info.title
            current_mr.description = mr_info.description or ""
            current_mr.author = mr_info.author.username
            current_mr.state = mr_info.state
            current_mr.mr_updated_at = mr_info.updated_at
            current_mr.commits_count = commits_count
            current_mr.changes_count = mr_info.changes_count or 0
            current_mr.additions_count = changes_stats.get('additions', 0)
            current_mr.deletions_count = changes_stats.get('deletions', 0)
            
            # 如果有提交，更新last_commit_sha
            if commits:
                current_mr.last_commit_sha = commits[0].id
            
            await session.commit()
            
            return {
                "success": True,
                "message": f"合并请求 '{current_mr.title}' 同步成功",
                "details": {
                    "id": current_mr.id,
                    "gitlab_id": current_mr.gitlab_id,
                    "title": current_mr.title,
                    "state": current_mr.state,
                    "commits_count": current_mr.commits_count,
                    "changes_count": current_mr.changes_count,
                    "additions_count": current_mr.additions_count,
                    "deletions_count": current_mr.deletions_count,
                    "last_commit_sha": current_mr.last_commit_sha,
                    "updated_at": current_mr.mr_updated_at.isoformat()
                }
            }
            
        except Exception as e:
            await session.rollback()
            logger.error(f"action: sync_single, project:{project.gitlab_id}, mr: {mr.gitlab_id}, error: {e}")
            return {
                "success": False,
                "message": f"同步失败: {str(e)}",
                "details": {}
            }

    async def _sync_project(self, session: AsyncSession, project_info: ProjectInfo) -> str:
        """同步单个项目"""
        # 查找现有项目
        result = await session.execute(
            select(Project).where(Project.gitlab_id == project_info.id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            # 创建新项目
            project = Project(
                gitlab_id=project_info.id,
                name=project_info.name,
                namespace=project_info.namespace.name,
                web_url=project_info.web_url,
                default_branch=project_info.default_branch,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(project)
            await session.flush()
            return "created"
        else:
            # 更新项目信息
            project.name = project_info.name
            project.namespace = project_info.namespace.name
            project.web_url = project_info.web_url
            project.default_branch = project_info.default_branch
            project.updated_at = datetime.utcnow()
            return "updated"
    
    async def _sync_project_merge_requests(self, session: AsyncSession, project: Project) -> Dict[str, int]:
        """同步单个项目的合并请求"""
        mrs_synced = 0
        mrs_updated = 0
        
        # 获取所有状态的合并请求
        states = ["opened", "closed", "merged"]
        
        for state in states:
            page = 1
            per_page = 100
            
            while True:
                try:
                    merge_requests, pagination = self.gitlab_client.get_merge_requests(
                        project_id=project.gitlab_id,
                        state=state,
                        page=page,
                        per_page=per_page
                    )
                    
                    if not merge_requests:
                        logger.debug(f"No {state} MRs found for project {project.name}")
                        break
                    
                    logger.info(f"Found {len(merge_requests)} {state} MRs for project {project.name} (page {page})")
                    
                    for mr_info in merge_requests:
                        try:
                            result = await self._sync_merge_request(session, mr_info, project)
                            if result == "created":
                                mrs_synced += 1
                                logger.info(f"type: mr action: created title: {mr_info.title}")
                            elif result == "updated":
                                mrs_updated += 1
                                logger.info(f"type: mr action: updated title: {mr_info.title}")
                        except Exception as e:
                            logger.error(f"type: mr action: sync title: {mr_info.title} error: {e}")
                            continue
                    
                    if not pagination.has_next:
                        logger.debug(f"Reached last page for {state} MRs")
                        break
                    
                    page += 1
                    
                except Exception as e:
                    logger.error(f"project: {project.name} state: {state} action: sync_mrs error: {e}")
                    # 继续处理下一个状态，而不是完全停止
                    break
        
        return {
            "synced": mrs_synced,
            "updated": mrs_updated
        }
    
    async def _sync_merge_request(self, session: AsyncSession, mr_info: MergeRequestInfo, project: Project) -> str:
        """同步单个合并请求"""
        gitlab_id = mr_info.iid
        
        # 查找现有合并请求
        result = await session.execute(
            select(MergeRequest).where(
                MergeRequest.gitlab_id == gitlab_id,
                MergeRequest.project_id == project.id
            )
        )
        mr = result.scalar_one_or_none()
        
        # 如果列表API已经提供了commits_count，优先使用
        commits_count = mr_info.commits_count or 0
        
        # 获取详细的变更统计信息
        changes_stats = self.gitlab_client.get_merge_request_changes_stats(project.gitlab_id, gitlab_id)
        
        # 获取提交信息
        commits = self.gitlab_client.get_merge_request_commits(project.gitlab_id, gitlab_id)
        commits_count = len(commits) if commits else 0
        
        # 获取最新提交的SHA
        last_commit_sha = commits[0].id if commits else None
        
        if not mr:
            # 创建新合并请求
            try:
                logger.debug(f"project: {project.name} action: creating_mr gitlab_id: {gitlab_id} title: {mr_info.title}")
                mr = MergeRequest(
                    gitlab_id=gitlab_id,
                    project_id=project.id,
                    title=mr_info.title,
                    description=mr_info.description or "",
                    author=mr_info.author.username,
                    source_branch=mr_info.source_branch,
                    target_branch=mr_info.target_branch,
                    state=mr_info.state,
                    mr_created_at=mr_info.created_at,
                    mr_updated_at=mr_info.updated_at,
                    commits_count=commits_count,
                    changes_count=mr_info.changes_count or 0,
                    additions_count=changes_stats.get('additions', 0),
                    deletions_count=changes_stats.get('deletions', 0),
                    last_commit_sha=last_commit_sha,
                )
                session.add(mr)
                await session.flush()
                logger.debug(f"project: {project.name} action: created_mr gitlab_id: {gitlab_id} db_id: {mr.id}")
                return "created"
            except IntegrityError as e:
                # 如果发生唯一约束冲突，回滚当前事务并重新查询
                await session.rollback()
                logger.warning(f"project: {project.name} action: integrity_error gitlab_id: {gitlab_id} error: {e}")
                
                # 重新查询，可能是并发创建导致的
                result = await session.execute(
                    select(MergeRequest).where(
                        MergeRequest.gitlab_id == gitlab_id,
                        MergeRequest.project_id == project.id
                    )
                )
                existing_mr = result.scalar_one_or_none()
                
                if existing_mr:
                    # 如果找到了，说明是并发创建，更新现有记录
                    logger.debug(f"project: {project.name} action: found_existing_mr gitlab_id: {gitlab_id} db_id: {existing_mr.id}")
                    existing_mr.title = mr_info.title
                    existing_mr.description = mr_info.description or ""
                    existing_mr.author = mr_info.author.username
                    existing_mr.state = mr_info.state
                    existing_mr.mr_updated_at = mr_info.updated_at
                    existing_mr.commits_count = commits_count
                    existing_mr.changes_count = mr_info.changes_count or 0
                    existing_mr.last_commit_sha = last_commit_sha
                    await session.flush()
                    return "updated"
                else:
                    # 如果还是找不到，重新抛出异常
                    logger.error(f"project: {project.name} action: integrity_error_no_existing gitlab_id: {gitlab_id} error: {e}")
                    raise e
        else:
            # 更新合并请求信息
            mr.title = mr_info.title
            mr.description = mr_info.description or ""
            mr.author = mr_info.author.username
            mr.state = mr_info.state
            mr.mr_updated_at = mr_info.updated_at
            mr.changes_count = mr_info.changes_count or 0
            mr.commits_count = commits_count
            mr.additions_count = changes_stats.get('additions', 0)
            mr.deletions_count = changes_stats.get('deletions', 0)
            mr.last_commit_sha = last_commit_sha
            
            return "updated"

    # ==================== 智能同步策略 ====================

    async def _determine_sync_strategy(self, session: AsyncSession) -> Dict[str, Any]:
        """确定同步策略 - 按照需求文档实现"""
        try:
            # 检查数据库中是否有项目
            result = await session.execute(select(Project))
            projects = result.scalars().all()
            
            if not projects:
                logger.info("type: sync reason: no_projects_in_db strategy: full")
                return {
                    "type": "full",
                    "reason": "数据库中没有项目，需要全量同步"
                }
            
            # 检查是否有新增项目
            new_projects = await self._check_for_new_projects(session)
            
            if new_projects:
                logger.info(f"type: sync reason: new_projects_found count: {len(new_projects)} strategy: full")
                return {
                    "type": "full",
                    "reason": f"发现 {len(new_projects)} 个新增项目，需要全量同步",
                    "new_projects": [p.name for p in new_projects]
                }
            
            # 执行增量同步
            logger.info("执行增量同步：处理新增MR，同步所有open的MR")
            return {
                "type": "incremental",
                "reason": "进行增量同步：处理新增MR，同步所有open的MR"
            }
            
        except Exception as e:
            logger.error(f"确定同步策略失败: {e}")
            # 默认执行增量同步
            return {
                "type": "incremental",
                "reason": "策略确定失败，执行增量同步"
            }

    async def _full_sync(self, session: AsyncSession) -> Dict[str, Any]:
        """全量同步"""
        # 同步项目
        projects_result = await self.sync_projects(session)
        
        # 同步合并请求
        merge_requests_result = await self.sync_merge_requests(session)
        
        # 提交事务
        await session.commit()
        
        return {
            "success": True,
            "message": f"全量同步完成 - 项目: {projects_result['total']}个, 合并请求: {merge_requests_result['total']}个",
            "strategy": "full",
            "projects": projects_result,
            "merge_requests": merge_requests_result
        }

    async def _incremental_sync(self, session: AsyncSession, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """增量同步"""
        # 增量同步项目
        projects_result = await self._sync_projects_incremental(session)
        
        # 增量同步合并请求
        merge_requests_result = await self._sync_merge_requests_incremental(session, strategy)
        
        # 提交事务
        await session.commit()
        
        return {
            "success": True,
            "message": f"增量同步完成 - 项目: {projects_result['total']}个, 合并请求: {merge_requests_result['total']}个",
            "strategy": "incremental",
            "projects": projects_result,
            "merge_requests": merge_requests_result
        }

    async def _sync_projects_incremental(self, session: AsyncSession) -> Dict[str, Any]:
        """增量同步项目 - 优化版本"""
        try:
            logger.info("type: projects state: incremental start")
            
            # 获取数据库中现有的GitLab项目ID
            result = await session.execute(select(Project.gitlab_id))
            existing_gitlab_ids = {row[0] for row in result.fetchall()}
            
            projects_synced = 0
            projects_updated = 0
            
            # 分页获取所有项目
            page = 1
            per_page = 100
            
            while True:
                try:
                    projects, pagination = self.gitlab_client.get_projects(page=page, per_page=per_page)
                    
                    if not projects:
                        break
                    
                    for project_info in projects:
                        try:
                            if project_info.id in existing_gitlab_ids:
                                # 更新现有项目
                                result = await self._sync_project(session, project_info)
                                if result == "updated":
                                    projects_updated += 1
                                    logger.debug(f"type: project action: updated name: {project_info.name} gitlab_id: {project_info.id}")
                            else:
                                # 新增项目
                                result = await self._sync_project(session, project_info)
                                if result == "created":
                                    projects_synced += 1
                                    logger.info(f"type: project action: created name: {project_info.name} gitlab_id: {project_info.id}")
                        except Exception as e:
                            logger.error(f"type: project action: sync name: {project_info.name} gitlab_id: {project_info.id} error: {e}")
                            continue
                    
                    if not pagination.has_next:
                        break
                    
                    page += 1
                    
                except Exception as e:
                    logger.error(f"type: projects action: get_list page: {page} error: {e}")
                    break
            
            total = projects_synced + projects_updated
            logger.info(f"type: projects state: incremental synced: {projects_synced} updated: {projects_updated} total: {total}")
            
            return {
                "synced": projects_synced,
                "updated": projects_updated,
                "total": total
            }
            
        except Exception as e:
            logger.error(f"type: projects state: incremental error: {e}")
            return {
                "synced": 0,
                "updated": 0,
                "total": 0
            }

    async def _sync_merge_requests_incremental(self, session: AsyncSession, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """增量同步合并请求"""
        mrs_synced = 0
        mrs_updated = 0
        
        try:
            # 获取所有项目
            result = await session.execute(select(Project))
            projects = result.scalars().all()
            
            for project in projects:
                try:
                    project_result = await self._sync_project_merge_requests_incremental(session, project, strategy)
                    mrs_synced += project_result["synced"]
                    mrs_updated += project_result["updated"]
                except Exception as e:
                    logger.error(f"project: {project.name} action: sync_mrs error: {e}")
                    continue
            
            total = mrs_synced + mrs_updated
            return {
                "synced": mrs_synced,
                "updated": mrs_updated,
                "total": total
            }
            
        except Exception as e:
            logger.error(f"type: mrs state: incremental_failed error: {e}")
            return {
                "synced": 0,
                "updated": 0,
                "total": 0
            }

    async def _sync_project_merge_requests_incremental(self, session: AsyncSession, project: Project, strategy: Dict[str, Any]) -> Dict[str, int]:
        """增量同步单个项目的合并请求 - 按照需求文档实现"""
        mrs_synced = 0
        mrs_updated = 0
        
        try:
            logger.info(f"project: {project.name} state: incremental start")
            
            # 1. 获取数据库中该项目的所有MR记录
            existing_mrs = await self._get_existing_mrs_for_project(session, project.id)
            existing_gitlab_ids = {mr.gitlab_id for mr in existing_mrs}
            
            # 2. 对所有open状态的MR进行同步
            logger.debug(f"project: {project.name} state: opened sync_start")
            open_result = await self._sync_mrs_by_state(session, project, "opened", existing_gitlab_ids)
            mrs_synced += open_result["synced"]
            mrs_updated += open_result["updated"]
            
            # 3. 对于ID最大的100条中缺失的gitlab id的MR进行同步
            logger.debug(f"project: {project.name} state: missing_in_top_100 sync_start")
            missing_result = await self._sync_missing_mrs_in_top_100(session, project, existing_gitlab_ids)
            mrs_synced += missing_result["synced"]
            mrs_updated += missing_result["updated"]
            
            # 4. 对gitlab中大于已记录gitlab id 的MR进行同步
            logger.debug(f"project: {project.name} state: greater_than_latest sync_start")
            new_result = await self._sync_new_mrs_greater_than_existing(session, project, existing_gitlab_ids)
            mrs_synced += new_result["synced"]
            mrs_updated += new_result["updated"]
            
            logger.info(f"project: {project.name} state: incremental synced: {mrs_synced} updated: {mrs_updated}")
            
            return {
                "synced": mrs_synced,
                "updated": mrs_updated
            }
            
        except Exception as e:
            logger.error(f"project: {project.name} state: incremental error: {e}")
            return {
                "synced": 0,
                "updated": 0
            }

    # ==================== 增量同步辅助方法 ====================

    async def _get_existing_mrs_for_project(self, session: AsyncSession, project_id: int) -> List[MergeRequest]:
        """获取项目中已存在的MR记录"""
        result = await session.execute(
            select(MergeRequest).where(MergeRequest.project_id == project_id)
        )
        return result.scalars().all()

    async def _sync_mrs_by_state(self, session: AsyncSession, project: Project, state: str, existing_gitlab_ids: set) -> Dict[str, int]:
        """同步指定状态的MR"""
        mrs_synced = 0
        mrs_updated = 0
        synced_mr_ids = []
        updated_mr_ids = []
        
        page = 1
        per_page = 100
        
        # 重新获取并同步MR
        page = 1
        while True:
            try:
                merge_requests, pagination = self.gitlab_client.get_merge_requests(
                    project_id=project.gitlab_id,
                    state=state,
                    page=page,
                    per_page=per_page
                )
                
                if not merge_requests:
                    break
                
                for mr_info in merge_requests:
                    try:
                        result = await self._sync_merge_request(session, mr_info, project)
                        if result == "created":
                            mrs_synced += 1
                            synced_mr_ids.append(mr_info.iid)
                            logger.debug(f"project: {project.name} action: create_mr title: {mr_info.title} gitlab_id: {mr_info.iid}")
                        elif result == "updated":
                            mrs_updated += 1
                            updated_mr_ids.append(mr_info.iid)
                            logger.debug(f"project: {project.name} action: update_mr title: {mr_info.title} gitlab_id: {mr_info.iid}")
                    except Exception as e:
                        logger.error(f"project: {project.name} action: sync_mr title: {mr_info.title} error: {e}")
                        continue
                
                if not pagination.has_next:
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"project: {project.name} state: {state} action: get_mrs_sync error: {e}")
                break
        
        # 记录详细的同步结果
        synced_ids_str = str(synced_mr_ids[:10]) if synced_mr_ids else "[]"
        updated_ids_str = str(updated_mr_ids[:10]) if updated_mr_ids else "[]"
        logger.info(f"project: {project.name} state: {state} synced: {mrs_synced} updated: {mrs_updated} synced_ids: {synced_ids_str} updated_ids: {updated_ids_str}")
        
        return {"synced": mrs_synced, "updated": mrs_updated}

    async def _sync_missing_mrs_in_top_100(self, session: AsyncSession, project: Project, existing_gitlab_ids: set) -> Dict[str, int]:
        """同步ID最大的100条中缺失的gitlab id的MR"""
        mrs_synced = 0
        mrs_updated = 0
        synced_mr_ids = []
        updated_mr_ids = []
        
        try:
            # 获取GitLab中最近的100个MR（按创建时间排序）
            merge_requests, _ = self.gitlab_client.get_merge_requests(
                project_id=project.gitlab_id,
                state="all",  # 获取所有状态
                page=1,
                per_page=100,
                order_by="created_at",  # GitLab API支持的值
                sort="desc"  # 按创建时间降序排列
            )
            
            if not merge_requests:
                return {"synced": 0, "updated": 0}
            
            # 按ID排序，获取ID最大的MR
            sorted_mrs = sorted(merge_requests, key=lambda x: x.iid, reverse=True)
            
            # 找出缺失的MR
            missing_mrs = []
            for mr_info in sorted_mrs:
                if mr_info.iid not in existing_gitlab_ids:
                    missing_mrs.append(mr_info)
            
            logger.debug(f"project: {project.name} state: missing_in_top_100 count: {len(missing_mrs)}")
            
            # 同步缺失的MR
            for mr_info in missing_mrs:
                try:
                    result = await self._sync_merge_request(session, mr_info, project)
                    if result == "created":
                        mrs_synced += 1
                        synced_mr_ids.append(mr_info.iid)
                        logger.debug(f"project: {project.name} action: create_missing_mr title: {mr_info.title} gitlab_id: {mr_info.iid}")
                    elif result == "updated":
                        mrs_updated += 1
                        updated_mr_ids.append(mr_info.iid)
                        logger.debug(f"project: {project.name} action: update_missing_mr title: {mr_info.title} gitlab_id: {mr_info.iid}")
                except Exception as e:
                    logger.error(f"project: {project.name} action: sync_missing_mr title: {mr_info.title} error: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"project: {project.name} state: missing_mrs error: {e}")
        
        # 记录详细的同步结果
        synced_ids_str = str(synced_mr_ids[:10]) if synced_mr_ids else "[]"
        updated_ids_str = str(updated_mr_ids[:10]) if updated_mr_ids else "[]"
        logger.info(f"project: {project.name} state: missing synced: {mrs_synced} updated: {mrs_updated} synced_ids: {synced_ids_str} updated_ids: {updated_ids_str}")
        
        return {"synced": mrs_synced, "updated": mrs_updated}

    async def _sync_new_mrs_greater_than_existing(self, session: AsyncSession, project: Project, existing_gitlab_ids: set) -> Dict[str, int]:
        """同步大于已记录gitlab id的MR - 优化版本"""
        mrs_synced = 0
        mrs_updated = 0
        synced_mr_ids = []
        updated_mr_ids = []
        
        if not existing_gitlab_ids:
            logger.info(f"project: {project.name} state: no_existing_mrs action: skip")
            return {"synced": 0, "updated": 0}
        
        try:
            # 获取最大的gitlab_id，标准化为latest MR ID
            latest_mr_id = max(existing_gitlab_ids)
            logger.debug(f"project: {project.name} latest_mr_id: {latest_mr_id}")
            
            # 使用更高效的方法：按创建时间获取最近的MR，然后检查ID
            page = 1
            per_page = 100
            found_new_mrs = False
            
            while True:
                try:
                    merge_requests, pagination = self.gitlab_client.get_merge_requests(
                        project_id=project.gitlab_id,
                        state="all",
                        page=page,
                        per_page=per_page,
                        order_by="created_at",  # GitLab API支持的值
                        sort="desc"
                    )
                    
                    if not merge_requests:
                        break
                    
                    # 检查当前页是否有大于latest_mr_id的MR
                    new_mrs_in_page = []
                    for mr_info in merge_requests:
                        if mr_info.iid > latest_mr_id:
                            new_mrs_in_page.append(mr_info)
                            found_new_mrs = True
                    
                    # 同步新MR
                    for mr_info in new_mrs_in_page:
                        try:
                            result = await self._sync_merge_request(session, mr_info, project)
                            if result == "created":
                                mrs_synced += 1
                                synced_mr_ids.append(mr_info.iid)
                                logger.debug(f"project: {project.name} action: create_new_mr title: {mr_info.title} gitlab_id: {mr_info.iid}")
                            elif result == "updated":
                                mrs_updated += 1
                                updated_mr_ids.append(mr_info.iid)
                                logger.debug(f"project: {project.name} action: update_new_mr title: {mr_info.title} gitlab_id: {mr_info.iid}")
                        except Exception as e:
                            logger.error(f"project: {project.name} action: sync_new_mr title: {mr_info.title} error: {e}")
                            continue
                    
                    # 如果当前页没有新MR，且已经找到过新MR，说明已经遍历完所有新MR
                    if not new_mrs_in_page and found_new_mrs:
                        break
                    
                    if not pagination.has_next:
                        break
                    
                    page += 1
                    
                except Exception as e:
                    logger.error(f"project: {project.name} action: get_mr_list error: {e}")
                    break
            
        except Exception as e:
            logger.error(f"project: {project.name} state: new_mrs error: {e}")
        
        # 记录详细的同步结果
        synced_ids_str = str(synced_mr_ids[:10]) if synced_mr_ids else "[]"
        updated_ids_str = str(updated_mr_ids[:10]) if updated_mr_ids else "[]"
        logger.info(f"project: {project.name} state: new synced: {mrs_synced} updated: {mrs_updated} synced_ids: {synced_ids_str} updated_ids: {updated_ids_str}")
        
        return {"synced": mrs_synced, "updated": mrs_updated}

    async def _check_for_new_projects(self, session: AsyncSession) -> List[ProjectInfo]:
        """检查是否有新增项目"""
        try:
            # 获取数据库中现有的GitLab项目ID
            result = await session.execute(select(Project.gitlab_id))
            existing_gitlab_ids = {row[0] for row in result.fetchall()}
            
            # 获取GitLab中的所有项目
            page = 1
            per_page = 100
            new_projects = []
            
            while True:
                try:
                    projects, pagination = self.gitlab_client.get_projects(page=page, per_page=per_page)
                    
                    if not projects:
                        break
                    
                    for project_info in projects:
                        if project_info.id not in existing_gitlab_ids:
                            new_projects.append(project_info)
                    
                    if not pagination.has_next:
                        break
                    
                    page += 1
                    
                except Exception as e:
                    logger.error(f"type: projects action: check_new error: {e}")
                    break
            
            if new_projects:
                logger.info(f"type: projects action: found_new count: {len(new_projects)}")
            
            return new_projects
            
        except Exception as e:
            logger.error(f"type: projects action: check_new error: {e}")
            return []

    # ==================== 其他功能方法 ====================

    async def get_mrs_needing_review(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """获取需要审查的MR列表"""
        try:
            # 查询opened状态的MR，检查是否需要审查
            result = await session.execute(
                select(MergeRequest).where(
                    MergeRequest.state == "opened"
                ).order_by(MergeRequest.mr_updated_at.desc())
            )
            mrs = result.scalars().all()
            
            mrs_needing_review = []
            
            for mr in mrs:
                # 检查是否有最新的审查记录
                needs_review = await self._check_mr_needs_review(session, mr)
                
                if needs_review:
                    mrs_needing_review.append({
                        "id": mr.id,
                        "gitlab_id": mr.gitlab_id,
                        "title": mr.title,
                        "author": mr.author,
                        "source_branch": mr.source_branch,
                        "target_branch": mr.target_branch,
                        "commits_count": mr.commits_count,
                        "changes_count": mr.changes_count,
                        "updated_at": mr.mr_updated_at,
                        "project": {
                            "id": mr.project.id,
                            "name": mr.project.name,
                            "namespace": mr.project.namespace
                        }
                    })
            
            return mrs_needing_review
            
        except Exception as e:
            logger.error(f"获取需要审查的MR失败: {e}")
            return []

    async def _check_mr_needs_review(self, session: AsyncSession, mr: MergeRequest) -> bool:
        """检查MR是否需要审查"""
        # 查询是否有审查记录
        result = await session.execute(
            select(CodeReview).where(
                CodeReview.merge_request_id == mr.id
            )
        )
        
        existing_review = result.scalar_one_or_none()
        return existing_review is None

    async def mark_mr_reviewed(self, session: AsyncSession, mr_id: int, commit_sha: str, review_data: Dict[str, Any]) -> bool:
        """标记MR已审查"""
        try:
            # 创建审查记录
            review = CodeReview(
                merge_request_id=mr_id,
                commit_sha=commit_sha,
                score=review_data.get("score"),
                review_content=review_data.get("review_content"),
                reviewer_type=review_data.get("reviewer_type", ""),
                status=review_data.get("status", "completed"),
                tokens_used=review_data.get("tokens_used")
            )
            
            session.add(review)
            await session.flush()
            
            # 更新MR的最后同步时间
            result = await session.execute(
                select(MergeRequest).where(MergeRequest.id == mr_id)
            )
            mr = result.scalar_one_or_none()
            
            await session.commit()
            return True
            
        except Exception as e:
            await session.rollback()
            logger.error(f"标记MR审查失败: {e}")
            return False

    @log_performance("sync_single_project_incremental")
    async def sync_single_project_incremental(self, session: AsyncSession, project_id: int) -> Dict[str, Any]:
        """增量同步单个项目的MR数据"""
        try:
            # 获取项目信息
            result = await session.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()
            
            if not project:
                return {
                    "success": False,
                    "message": f"项目不存在: {project_id}",
                    "project_id": project_id
                }
            
            logger.info(f"project: {project.name} state: single_sync start")
            
            # 执行增量同步
            sync_result = await self._sync_project_merge_requests_incremental(session, project, {})
            
            logger.info(f"project: {project.name} state: single_sync completed synced: {sync_result['synced']} updated: {sync_result['updated']}")
            
            # 提交事务
            await session.commit()
            
            return {
                "success": True,
                "message": f"项目 {project.name} 同步完成",
                "project_id": project_id,
                "project_name": project.name,
                "synced": sync_result["synced"],
                "updated": sync_result["updated"],
                "total": sync_result["synced"] + sync_result["updated"]
            }
            
        except Exception as e:
            await session.rollback()
            logger.error(f"project: {project_id} state: single_sync error: {e}")
            return {
                "success": False,
                "message": f"项目同步失败: {str(e)}",
                "project_id": project_id
            }



