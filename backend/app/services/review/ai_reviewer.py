"""
AI代码审查器 - 重构版本
"""
from typing import Dict, Any, Optional, List
import random

from sqlalchemy import select
from app.core.config import settings
from app.core.logging import get_logger
from app.services.review.ai_interfaces import (
    AIReviewerInterface, ReviewRequest, ReviewResult, ModelConfig, ModelProvider,
    PromptTemplate, ContextInfo
)
from app.services.ai.ai_service import ai_service
from app.services.review.prompt_renderer import Jinja2PromptRenderer, AIResultParser
from app.services.review.context_builder import AIContextBuilder
from app.services.review.template_builder import ReviewTemplateBuilder

logger = get_logger("ai_reviewer")


class AIReviewer(AIReviewerInterface):
    """AI代码审查器 - 重构版本"""
    
    def __init__(self):
        self.prompt_renderer = Jinja2PromptRenderer()
        self.result_parser = AIResultParser()
        self.context_builder = AIContextBuilder()
        self.template_builder = ReviewTemplateBuilder()
    
    async def review(self, request: ReviewRequest) -> ReviewResult:
        """执行AI审查"""
        try:
            # 1. 获取或使用默认模型配置
            model_config = request.model_config or self.get_default_model_config()
            
            # 2. 获取或使用默认模板
            template = request.template or await self._get_default_template()
            logger.debug(f"template character: {len(template.content)}")
            
            # 3. 渲染Prompt
            prompt = self.prompt_renderer.render_prompt(template, request.context, request.code_diff)
            logger.debug(f"prompt character: {len(prompt)}")
            # 4. 生成AI响应
            logger.info(f"开始AI审查，使用模型: {model_config.provider.value}/{model_config.model_name}")
            ai_response = await ai_service.generate_response(
                prompt=prompt,
                system_prompt="你是一个专业的代码审查专家，请对提供的代码进行全面审查。",
                model_id=model_config.model_name,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens
            )
            
            # 7. 解析结果
            try:
                result = self.result_parser.parse_response(
                    ai_response["content"], 
                    None  # 输出格式规范由解析器统一管理，不需要从模板传入
                )
                
                # 8. 添加元数据（无论解析是否成功都保存token信息）
                result.tokens_used = ai_response.get("tokens_used", 0)
                result.direct_token = ai_response.get("direct_token", 0)
                result.cache_token = ai_response.get("cache_token", 0)
                result.prompt_token = ai_response.get("prompt_token", 0)
                result.completion_token = ai_response.get("completion_token", 0)
                result.model_used = ai_response.get("model", "")
                result.template_used = template.name
                result.request_duration = ai_response.get("request_duration", None)
                
                # 9. 验证结果
                if not self.result_parser.validate_result(result):
                    logger.error("AI响应验证失败")
                    # 验证失败时，创建一个包含token信息的错误结果
                    return self._create_error_result("AI响应格式验证失败，无法解析审查结果", ai_response)
                
            except Exception as parse_error:
                logger.error(f"解析AI响应失败: {str(parse_error)}")
                # 解析失败时，创建一个包含token信息的错误结果
                return self._create_error_result(f"解析AI响应失败: {str(parse_error)}", ai_response)
            
            logger.info(f"AI审查完成，评分: {result.score}, 使用token: {result.tokens_used} ,cache_token: {result.cache_token}, direct_token: {result.direct_token}")
            return result
            
        except Exception as e:
            logger.error(f"AI审查失败: {str(e)}")
            # 如果有AI响应，传递token信息
            ai_response_data = None
            if 'ai_response' in locals():
                ai_response_data = ai_response
            return self._create_error_result(str(e), ai_response_data)
    
    def get_supported_providers(self) -> List[ModelProvider]:
        """获取支持的模型提供商"""
        return [ModelProvider.DEEPSEEK, ModelProvider.OPENAI, ModelProvider.CLAUDE]
    
    def get_default_model_config(self) -> ModelConfig:
        """获取默认模型配置"""
        return ai_service.get_model_config()
    
    async def _get_default_template(self) -> PromptTemplate:
        """获取默认模板 - 优先使用ID=1的内置模板"""
        try:
            # 尝试从数据库获取ID=1的内置模板
            from app.core.database import AsyncSessionLocal
            from app.models.prompt_template import PromptTemplate as DBPromptTemplate
            
            async with AsyncSessionLocal() as session:
                # 优先查找ID=1的内置模板
                db_template = await session.get(DBPromptTemplate, 1)
                
                if db_template and db_template.is_active:
                    # 转换为AI审查器使用的PromptTemplate格式
                    return PromptTemplate(
                        name=db_template.name,
                        content=db_template.template_content,
                        variables_schema=db_template.variables_schema or [],  # 现在是变量名称列表
                        output_format=None,  # 输出格式规范由解析器统一管理
                        description=db_template.description
                    )
                
                # 如果没有ID=1的模板，查找其他默认模板
                stmt = select(DBPromptTemplate).where(
                    DBPromptTemplate.is_default == True,
                    DBPromptTemplate.is_active == True
                )
                result = await session.execute(stmt)
                db_template = result.scalar_one_or_none()
                
                if db_template:
                    # 转换为AI审查器使用的PromptTemplate格式
                    return PromptTemplate(
                        name=db_template.name,
                        content=db_template.template_content,
                        variables_schema=db_template.variables_schema or [],  # 现在是变量名称列表
                        output_format=None,  # 输出格式规范由解析器统一管理
                        description=db_template.description
                    )
        except Exception as e:
            logger.warning(f"从数据库获取默认模板失败: {str(e)}")
        
        # 降级到内置模板
        return self._get_builtin_template()
    
    async def get_template_by_name(self, template_name: str) -> Optional[PromptTemplate]:
        """根据名称获取模板"""
        try:
            from app.core.database import AsyncSessionLocal
            from app.models.prompt_template import PromptTemplate as DBPromptTemplate
            
            async with AsyncSessionLocal() as session:
                stmt = select(DBPromptTemplate).where(
                    DBPromptTemplate.name == template_name,
                    DBPromptTemplate.is_active == True
                )
                result = await session.execute(stmt)
                db_template = result.scalar_one_or_none()
                
                if db_template:
                    return PromptTemplate(
                        name=db_template.name,
                        content=db_template.template_content,
                        variables_schema=db_template.variables_schema or {},
                        output_format=db_template.output_format or {},
                        description=db_template.description
                    )
        except Exception as e:
            logger.error(f"获取模板失败: {str(e)}")
        
        return None
    
    def _get_builtin_template(self) -> PromptTemplate:
        """获取内置模板 - 使用新的模板构建器"""
        from app.services.review.template_builder import ReviewTemplateBuilder
        
        # 定义核心变量列表
        core_variables = ["project_name", "mr_title", "source_branch", "target_branch"]
        
        # 创建新的模板构建器实例，确保使用最新的模板内容
        template_builder = ReviewTemplateBuilder()
        template_content = template_builder.build_standard_template(selected_variables=core_variables)
        used_variables = template_builder.get_template_variables_schema(selected_variables=core_variables)
        
        return PromptTemplate(
            name="内置审查模板",
            content=template_content,
            variables_schema=used_variables,  # 只存储变量名称列表
            output_format=None,  # 输出格式规范由解析器统一管理
            description="内置AI代码审查模板 - 按照审查定义构建，会根据MR标题前缀自动判断审查重点"
        )
    
    
    def _create_error_result(self, error_message: str, ai_response: Dict[str, Any] = None) -> ReviewResult:
        """创建错误结果"""
        # 如果有AI响应，尝试保存token信息
        tokens_used = 0
        direct_token = 0
        cache_token = 0
        prompt_token = 0
        completion_token = 0
        model_used = ""
        request_duration = None
        
        if ai_response:
            tokens_used = ai_response.get("tokens_used", 0)
            direct_token = ai_response.get("direct_token", 0)
            cache_token = ai_response.get("cache_token", 0)
            prompt_token = ai_response.get("prompt_token", 0)
            completion_token = ai_response.get("completion_token", 0)
            model_used = ai_response.get("model", "")
            request_duration = ai_response.get("request_duration", None)
        
        return ReviewResult(
            score=0,
            level="critical",
            summary=f"AI审查失败: {error_message}",
            categories=[],
            issues=[],
            tokens_used=tokens_used,
            direct_token=direct_token,
            cache_token=cache_token,
            prompt_token=prompt_token,
            completion_token=completion_token,
            model_used=model_used,
            error_message=error_message,
            request_duration=request_duration,
            # 向后兼容字段
            score_details={
                "code_quality": {"score": 0, "reason": f"审查失败: {error_message}"},
                "correctness": {"score": 0, "reason": f"审查失败: {error_message}"},
                "performance": {"score": 0, "reason": f"审查失败: {error_message}"},
                "security": {"score": 0, "reason": f"审查失败: {error_message}"},
                "testing": {"score": 0, "reason": f"审查失败: {error_message}"}
            },
            strengths=[],
            improvements=[],
            review_content=f"AI审查失败: {error_message}"
        )

