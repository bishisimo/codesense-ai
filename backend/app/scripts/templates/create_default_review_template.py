#!/usr/bin/env python3
"""
创建默认的审查模板
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.services.review_template.template_service import TemplateService
from app.core.logging import get_logger

logger = get_logger("create_default_template")


async def create_builtin_template():
    """创建或更新内置审查模板 (固定ID=1)"""
    async with AsyncSessionLocal() as session:
        template_service = TemplateService()
        
        # 创建标准模板
        template_data = template_service.create_standard_template(
            name="内置审查模板",
            description="按照审查定义构建的内置AI代码审查模板，会根据MR标题前缀自动判断审查重点",
            selected_variables=[
                "project_name", "mr_title", "source_branch", "target_branch",
                "commits_count", "changes_count", "additions_count", "deletions_count",
                "complexity_analysis", "commit_statistics", "diff_info"
            ],
            custom_instructions=None,  # 不添加自定义指令，因为审查重点已经在模板中定义
            template_source="system"
        )
        
        # 检查是否已存在ID=1的模板
        from app.models.prompt_template import PromptTemplate
        
        existing_template = await session.get(PromptTemplate, 1)
        
        if existing_template:
            # 更新现有模板
            existing_template.name = template_data["name"]
            existing_template.description = template_data["description"]
            existing_template.template_content = template_data["template_content"]
            existing_template.variables_schema = template_data["variables_schema"]
            existing_template.output_format = template_data["output_format"]
            existing_template.template_source = template_data["template_source"]
            existing_template.is_default = True
            existing_template.is_active = True
            
            await session.commit()
            await session.refresh(existing_template)
            logger.info(f"成功更新内置模板: {existing_template.name} (ID: {existing_template.id})")
            return existing_template
        else:
            # 创建新模板，强制使用ID=1
            template = PromptTemplate(
                id=1,  # 固定ID
                name=template_data["name"],
                description=template_data["description"],
                template_content=template_data["template_content"],
                variables_schema=template_data["variables_schema"],
                output_format=template_data["output_format"],
                created_by="system",
                is_default=True,
                is_active=True,
                template_source=template_data["template_source"]
            )
            
            session.add(template)
            await session.commit()
            await session.refresh(template)
            logger.info(f"成功创建内置模板: {template.name} (ID: {template.id})")
            return template
