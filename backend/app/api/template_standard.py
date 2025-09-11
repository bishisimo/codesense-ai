"""
标准化模板创建API
"""
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.prompt_template import PromptTemplate
from app.schemas.prompt_template import PromptTemplateResponse
from app.services.review_template.template_service import TemplateService
from app.core.logging import get_logger

logger = get_logger("template_standard")

router = APIRouter()

# 依赖项
SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

# 模板服务实例
template_service = TemplateService()


@router.post("/create-standard", summary="创建标准化审查模板")
async def create_standard_template(
    session: SessionDep,
    current_user: UserDep,
    name: str,
    description: str,
    selected_variables: Optional[List[str]] = None,
    custom_instructions: Optional[str] = None,
    is_default: bool = False
):
    """创建标准化的审查模板"""
    try:
        # 检查模板名称是否已存在
        existing = await session.scalar(
            select(PromptTemplate).where(PromptTemplate.name == name)
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="模板名称已存在"
            )
        
        # 使用模板服务创建标准化模板
        template_data = template_service.create_standard_template(
            name=name,
            description=description,
            selected_variables=selected_variables,
            custom_instructions=custom_instructions,
            template_source="manual"
        )
        
        # 保存到数据库
        template = await template_service.create_template(
            session=session,
            name=template_data["name"],
            description=template_data["description"],
            template_content=template_data["template_content"],
            variables_schema=template_data["variables_schema"],
            output_format=template_data["output_format"],
            created_by=current_user.get("username", "admin"),
            is_default=is_default,
            template_source=template_data["template_source"]
        )
        
        if template:
            response_data = PromptTemplateResponse.model_validate(template)
            return response_data
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建模板失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建标准化模板失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建模板失败: {str(e)}"
        )
