"""
模板服务
"""
from typing import Dict, Any, List, Optional

from jinja2 import Environment, Template, StrictUndefined, TemplateError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.prompt_template import PromptTemplate
from app.services.review_template.template_variables import TemplateVariables
from app.core.logging import logger
from app.services.review.template_builder import ReviewTemplateBuilder


class TemplateRenderError(Exception):
    """模板渲染错误"""
    pass


class TemplateService:
    """模板服务"""
    
    def __init__(self):
        self.env = Environment(
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False
        )
        
        # 使用新的变量定义
        self.template_variables = TemplateVariables()
        self.template_builder = ReviewTemplateBuilder()
        
    def get_core_variables(self) -> Dict[str, str]:
        """获取核心变量列表"""
        return self.template_variables.get_core_variables_dict()
        
    def get_extended_variables(self) -> Dict[str, str]:
        """获取扩展变量列表"""
        return self.template_variables.get_extended_variables_dict()
        
    def get_all_variables(self) -> Dict[str, str]:
        """获取所有变量列表"""
        return self.template_variables.get_variables_dict()
    
    def get_example_data(self) -> Dict[str, Any]:
        """获取变量示例数据，用于模板验证和测试"""
        return self.template_variables.get_example_data()
        
    def render_template(self, template_content: str, render_data: Dict[str, Any]) -> str:
        """渲染模板"""
        try:
            template = self.env.from_string(template_content)
            return template.render(**render_data)
        except TemplateError as e:
            logger.error(f"模板渲染失败: {str(e)}")
            raise TemplateRenderError(f"模板渲染失败: {str(e)}")
        except Exception as e:
            logger.error(f"模板渲染异常: {str(e)}")
            raise TemplateRenderError(f"模板渲染异常: {str(e)}")
            

        
    def _extract_template_variables(self, template_content: str) -> List[str]:
        """提取模板中使用的变量"""
        try:
            template = self.env.from_string(template_content)
            # 这里简化处理，实际可以通过解析AST来获取变量
            import re
            variables = re.findall(r'\{\{\s*(\w+)\s*\}\}', template_content)
            return list(set(variables))
        except Exception:
            return []
            


    async def get_default_template(self, session: AsyncSession) -> Optional[PromptTemplate]:
        """获取默认模板"""
        try:
            result = await session.execute(
                select(PromptTemplate).where(
                    PromptTemplate.is_default == True,
                    PromptTemplate.is_active == True
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取默认模板失败: {str(e)}")
            return None

    async def get_template_by_name(self, session: AsyncSession, name: str) -> Optional[PromptTemplate]:
        """根据名称获取模板"""
        try:
            result = await session.execute(
                select(PromptTemplate).where(
                    PromptTemplate.name == name,
                    PromptTemplate.is_active == True
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取模板失败: {str(e)}")
            return None

    async def get_template_by_id(self, session: AsyncSession, template_id: int) -> Optional[PromptTemplate]:
        """根据ID获取模板"""
        try:
            result = await session.execute(
                select(PromptTemplate).where(
                    PromptTemplate.id == template_id,
                    PromptTemplate.is_active == True
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取模板失败: {str(e)}")
            return None

    async def list_templates(
            self, 
            session: AsyncSession, 
            skip: int = 0, 
            limit: int = 100,
            is_active: Optional[bool] = None
    ) -> List[PromptTemplate]:
        """获取模板列表"""
        try:
            query = select(PromptTemplate)
            
            if is_active is not None:
                query = query.where(PromptTemplate.is_active == is_active)
            
            query = query.offset(skip).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取模板列表失败: {str(e)}")
            return []

    def create_standard_template(
            self,
            name: str,
            description: str,
            selected_variables: List[str] = None,
            custom_instructions: str = None,
            template_source: str = "manual"
    ) -> Dict[str, Any]:
        """创建标准化模板"""
        if selected_variables is None:
            selected_variables = ["project_name", "mr_title", "source_branch", "target_branch"]
        
        # 使用模板构建器生成模板内容
        template_content = self.template_builder.build_standard_template(
            selected_variables=selected_variables,
            custom_instructions=custom_instructions
        )
        
        # 获取模板使用的变量列表
        used_variables = self.template_builder.get_template_variables_schema(selected_variables)
        
        return {
            "name": name,
            "description": description,
            "template_content": template_content,
            "variables_schema": used_variables,  # 只存储变量名称列表
            "output_format": None,  # 输出格式规范由后端统一管理
            "template_source": template_source
        }
    
    async def create_template(
            self,
            session: AsyncSession,
            name: str,
            description: str,
            template_content: str,
            variables_schema: Dict[str, Any],
            output_format: Dict[str, Any],
            created_by: str,
            is_default: bool = False,
            template_source: str = "manual"
    ) -> Optional[PromptTemplate]:
        """创建新模板"""
        try:
            # 如果设置为默认模板，先取消其他默认模板
            if is_default:
                await session.execute(
                    select(PromptTemplate).where(PromptTemplate.is_default == True)
                )
                existing_defaults = await session.execute(
                    select(PromptTemplate).where(PromptTemplate.is_default == True)
                )
                for template in existing_defaults.scalars().all():
                    template.is_default = False

            template = PromptTemplate(
                name=name,
                description=description,
                template_content=template_content,
                variables_schema=variables_schema,
                output_format=output_format,
                created_by=created_by,
                is_default=is_default,
                is_active=True,
                template_source=template_source
            )
            
            session.add(template)
            await session.flush()
            await session.refresh(template)
            await session.commit()
            
            return template
        except Exception as e:
            logger.error(f"创建模板失败: {str(e)}")
            await session.rollback()
            return None

    async def update_template(
            self,
            session: AsyncSession,
            template_id: int,
            **kwargs
    ) -> Optional[PromptTemplate]:
        """更新模板"""
        try:
            template = await self.get_template_by_id(session, template_id)
            if not template:
                return None
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            
            await session.flush()
            await session.refresh(template)
            
            return template
        except Exception as e:
            logger.error(f"更新模板失败: {str(e)}")
            await session.rollback()
            return None

    async def delete_template(self, session: AsyncSession, template_id: int) -> bool:
        """删除模板"""
        try:
            template = await self.get_template_by_id(session, template_id)
            if not template:
                return False
            
            # 软删除：设置为非激活状态
            template.is_active = False
            await session.flush()
            
            return True
        except Exception as e:
            logger.error(f"删除模板失败: {str(e)}")
            await session.rollback()
            return False

    async def set_default_template(self, session: AsyncSession, template_id: int) -> bool:
        """设置默认模板"""
        try:
            # 取消所有现有默认模板
            await session.execute(
                select(PromptTemplate).where(PromptTemplate.is_default == True)
            )
            existing_defaults = await session.execute(
                select(PromptTemplate).where(PromptTemplate.is_default == True)
            )
            for template in existing_defaults.scalars().all():
                template.is_default = False
            
            # 设置新的默认模板
            template = await self.get_template_by_id(session, template_id)
            if not template:
                return False
            
            template.is_default = True
            await session.flush()
            
            return True
        except Exception as e:
            logger.error(f"设置默认模板失败: {str(e)}")
            await session.rollback()
            return False
