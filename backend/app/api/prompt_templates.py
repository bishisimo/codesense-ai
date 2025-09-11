"""
AI审查Prompt模板管理API路由
"""
import re
from typing import Annotated, Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.prompt_template import PromptTemplate
from app.schemas.prompt_template import (
    PromptTemplateCreate, PromptTemplateUpdate, PromptTemplateResponse,
    PromptTemplateListResponse, TemplateRenderRequest, TemplateRenderResponse,
    TemplateTestRequest, TemplateTestResponse, TemplateVariablesResponse,
    TemplateVariableInfo, AITemplateGenerationRequest, AITemplateGenerationResponse
)
from app.services.review_template.template_service import TemplateService, TemplateRenderError
from app.services.ai import template_generator
from app.services.task import task_manager, TaskStatus
from app.services.review_template.template_variables import TemplateVariables
from app.core.logging import get_logger

logger = get_logger("prompt_templates")

router = APIRouter()

# 依赖项
SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

# 模板服务实例
template_service = TemplateService()


@router.get("", summary="获取Prompt模板列表")
async def get_prompt_templates(
    session: SessionDep,
    current_user: UserDep,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="模板名称筛选"),
    is_active: Optional[bool] = Query(None, description="是否激活筛选"),
    generation_status: Optional[str] = Query(None, description="生成状态筛选"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向")
):
    """获取Prompt模板列表，支持分页、筛选和排序"""
    
    # 构建查询
    query = select(PromptTemplate)
    
    # 添加筛选条件
    filters = []
    if name:
        filters.append(PromptTemplate.name.ilike(f"%{name}%"))
    if is_active is not None:
        filters.append(PromptTemplate.is_active == is_active)
    if generation_status:
        filters.append(PromptTemplate.generation_status == generation_status)
    
    if filters:
        query = query.where(and_(*filters))
    
    # 添加排序
    sort_column = getattr(PromptTemplate, sort_by, PromptTemplate.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # 计算总数
    count_query = select(func.count(PromptTemplate.id))
    if filters:
        count_query = count_query.where(and_(*filters))
    
    total = await session.scalar(count_query) or 0
    
    # 分页
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    
    # 执行查询
    result = await session.execute(query)
    templates = result.scalars().all()
    
    # 转换为响应模型
    items = [PromptTemplateResponse.model_validate(template) for template in templates]
    
    response_data = PromptTemplateListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )
    
    return response_data


@router.post("", summary="创建Prompt模板")
async def create_prompt_template(
    session: SessionDep,
    current_user: UserDep,
    template: PromptTemplateCreate
):
    """创建新的Prompt模板"""
    
    # 检查模板名称是否已存在
    existing = await session.scalar(
        select(PromptTemplate).where(PromptTemplate.name == template.name)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="模板名称已存在"
        )
    
    # 已移除模板语法校验（参见格式校验移除设计）。
    
    # 创建模板
    db_template = PromptTemplate(
        name=template.name,
        description=template.description,
        template_content=template.template_content,
        variables_schema=template.variables_schema,
        output_format=template.output_format,
        is_active=template.is_active,
        generation_status="pending",  # 新创建的模板状态为pending
        validation_errors=None,  # 新创建的模板没有验证错误
        ai_generated=False,  # 手动创建的模板
        created_by=current_user.get("username", "admin")
    )
    
    session.add(db_template)
    await session.commit()
    await session.refresh(db_template)
    
    response_data = PromptTemplateResponse.model_validate(db_template)
    return response_data


@router.get("/variables", summary="获取模板变量")
async def get_template_variables(
    current_user: UserDep
):
    """获取可用的模板变量"""
    
    from app.services.review_template.template_variables import TemplateVariables
    
    template_variables = TemplateVariables()
    all_variables = template_variables.get_all_variables()
    
    variables = []
    
    # 转换变量定义
    for var in all_variables:
        variables.append(TemplateVariableInfo(
            name=var.name,
            description=var.description,
            type=var.type,
            required=var.required,
            example=var.example,
            group=var.group
        ))
    
    response_data = TemplateVariablesResponse(variables=variables)
    return response_data


@router.get("/{template_id}", summary="获取Prompt模板详情")
async def get_prompt_template(
    session: SessionDep,
    current_user: UserDep,
    template_id: int
):
    """获取Prompt模板详情"""
    
    template = await session.get(PromptTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    response_data = PromptTemplateResponse.model_validate(template)
    return response_data


@router.put("/{template_id}", summary="更新Prompt模板")
async def update_prompt_template(
    template_id: int,
    template_update: PromptTemplateUpdate,
    session: SessionDep,
    current_user: UserDep
):
    """更新Prompt模板"""
    template = await session.get(PromptTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 检查是否为系统默认模板
    if template.created_by == "system":
        raise HTTPException(status_code=400, detail="系统默认模板不能修改")
    
    # 更新模板字段
    for field, value in template_update.dict(exclude_unset=True).items():
        setattr(template, field, value)
    
    template.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(template)
    
    response_data = PromptTemplateResponse.model_validate(template)
    return response_data


@router.delete("/{template_id}", summary="删除Prompt模板")
async def delete_prompt_template(
    template_id: int,
    session: SessionDep,
    current_user: UserDep
):
    """删除Prompt模板"""
    template = await session.get(PromptTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 检查是否为系统默认模板
    if template.created_by == "system":
        raise HTTPException(status_code=400, detail="系统默认模板不能删除")
    
    # 检查是否为当前默认模板
    if template.is_default:
        raise HTTPException(status_code=400, detail="默认模板不能删除，请先设置其他模板为默认")
    
    await session.delete(template)
    await session.commit()
    
    return {"message": "模板删除成功"}


@router.post("/{template_id}/set-default", summary="设置默认模板")
async def set_default_template(
    session: SessionDep,
    current_user: UserDep,
    template_id: int
):
    """设置默认模板"""
    
    template = await session.get(PromptTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    success = await template_service.set_default_template(session, template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="设置默认模板失败"
        )
    # 持久化修改，确保默认模板切换真正生效
    await session.commit()
    
    return {"message": "默认模板设置成功"}


@router.post("/{template_id}/render", summary="渲染模板")
async def render_template(
    session: SessionDep,
    current_user: UserDep,
    template_id: int,
    render_request: TemplateRenderRequest
):
    """渲染模板"""
    
    template = await session.get(PromptTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    try:
        rendered_content = template_service.render_template(
            template.template_content,
            render_request.render_data
        )
        
        # 获取使用的变量
        variables_used = template_service._extract_template_variables(template.template_content)
        
        response_data = TemplateRenderResponse(
            rendered_content=rendered_content,
            variables_used=variables_used,
            errors=[]
        )
        return response_data
    except TemplateRenderError as e:
        response_data = TemplateRenderResponse(
            rendered_content="",
            variables_used=[],
            errors=[str(e)]
        )
        return response_data


@router.post("/{template_id}/test", summary="测试模板")
async def test_template(
    session: SessionDep,
    current_user: UserDep,
    template_id: int,
    test_request: TemplateTestRequest
):
    """测试模板"""
    
    template = await session.get(PromptTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    try:
        # 为测试提供默认数据
        test_data = test_request.test_data.copy()
        
        # 如果测试数据为空，使用变量定义中的示例数据
        if not test_data:
            test_data = template_service.get_example_data()
        
        # 渲染模板
        rendered_prompt = template_service.render_template(
            template.template_content,
            test_data
        )
        
        response_data = TemplateTestResponse(
            rendered_prompt=rendered_prompt,
            validation_result={
                "valid": True,
                "errors": [],
                "warnings": []
            },
            test_success=True
        )
        return response_data
    except TemplateRenderError as e:
        response_data = TemplateTestResponse(
            rendered_prompt="",
            validation_result={
                "valid": False,
                "errors": [str(e)],
                "warnings": []
            },
            test_success=False
        )
        return response_data


@router.post("/ai-generate", summary="AI生成模板")
async def generate_ai_template(
    session: SessionDep,
    current_user: UserDep,
    generation_request: AITemplateGenerationRequest
):
    """使用AI生成Prompt模板（异步任务）"""
    
    try:
        # 提交异步任务
        task_id = await task_manager.submit_task(
            "ai_template_generation",
            prompt=generation_request.prompt,
            selected_variables=generation_request.selected_variables,
            template_name=generation_request.template_name,
            description=generation_request.description
        )
        
        return {
            "task_id": task_id,
            "message": "AI生成任务已提交，请使用任务ID查询进度"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交AI生成任务失败: {str(e)}"
        )


@router.get("/ai-generate/{task_id}/status", summary="查询AI生成任务状态")
async def get_ai_generation_status(
    task_id: str,
    current_user: UserDep
):
    """查询AI生成任务状态"""
    
    task_result = task_manager.get_task_status(task_id)
    if not task_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return task_result.to_dict()


@router.post("/ai-generate/{task_id}/cancel", summary="取消AI生成任务")
async def cancel_ai_generation(
    task_id: str,
    current_user: UserDep
):
    """取消AI生成任务"""
    
    success = task_manager.cancel_task(task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法取消任务，任务可能已完成或不存在"
        )
    
    return {"message": "任务已取消"}


@router.get("/ai-generate/{task_id}/result", summary="获取AI生成结果")
async def get_ai_generation_result(
    task_id: str,
    current_user: UserDep
):
    """获取AI生成结果"""
    
    task_result = task_manager.get_task_status(task_id)
    if not task_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    if task_result.status == TaskStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务尚未开始"
        )
    
    if task_result.status == TaskStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务正在执行中"
        )
    
    if task_result.status == TaskStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务执行失败: {task_result.error}"
        )
    
    if task_result.status == TaskStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务已取消"
        )
    
    # 任务完成，返回结果
    result = task_result.result
    template_content = result["content"]
    
    # 清理生成的模板内容
    template_content = _clean_ai_generated_content(template_content)
    
    # 验证模板变量的合法性
    template_content = _validate_and_fix_template_variables(template_content)
    
    # 提取实际使用的变量
    variables_used = template_service._extract_template_variables(template_content)
    
    # 获取AI统计信息
    tokens_used = result.get("tokens_used", 0)
    generation_time = result.get("generation_time", 0)
    
    response_data = AITemplateGenerationResponse(
        template_content=template_content,
        variables_used=variables_used,
        tokens_used=tokens_used,
        generation_time=generation_time
    )
    
    return response_data


def _clean_ai_generated_content(content: str) -> str:
    """清理AI生成的模板内容"""
    # 移除代码块包裹
    content = re.sub(r'^```(?:jinja2?|markdown|md)?\s*\n', '', content, flags=re.MULTILINE)
    content = re.sub(r'\n```\s*$', '', content, flags=re.MULTILINE)
    
    # 移除常见的AI免责声明
    patterns_to_remove = [
        r'^\s*---\s*\n\*本报告由AI代码审查系统生成，仅供参考\*\s*\n?',
        r'^\s*\*本报告由AI.*?生成.*?\*\s*\n?',
        r'^\s*注意：.*?AI.*?生成.*?\n?',
        r'^\s*Note:.*?generated.*?AI.*?\n?',
        r'^\s*Disclaimer:.*?\n?',
        r'^\s*声明：.*?\n?',
        r'^\s*以下是生成的.*?模板.*?\n?',
        r'^\s*Here.*?generated.*?template.*?\n?',
    ]
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content, flags=re.MULTILINE | re.IGNORECASE)
    
    # 移除开头和结尾的空白行
    content = content.strip()
    
    # 移除多余的连续空行
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    return content


def _validate_and_fix_template_variables(content: str) -> str:
    """验证并修复模板中的变量使用"""
    from app.services.review_template.template_variables import TemplateVariables
    
    # 获取系统定义的所有变量
    allowed_variables = set(TemplateVariables.get_variables_dict().keys())
    
    # 查找模板中使用的所有变量
    variable_pattern = r'\{\{\s*(\w+(?:\.\w+)*)(?:\s*\|[^}]*)?\s*\}\}'
    used_variables = re.findall(variable_pattern, content)
    
    # 处理复杂变量（如 complexity_analysis.complexity_level）
    base_variables = set()
    for var in used_variables:
        base_var = var.split('.')[0]  # 获取基础变量名
        base_variables.add(base_var)
    
    # 查找未定义的变量
    undefined_variables = base_variables - allowed_variables
    
    if undefined_variables:
        logger.warning(f"发现未定义的变量: {undefined_variables}")
        
        # 移除或替换未定义的变量
        for undefined_var in undefined_variables:
            # 移除包含未定义变量的整行
            pattern = rf'^.*\{{\{{\s*{re.escape(undefined_var)}[^}}]*\}}\}}.*$'
            content = re.sub(pattern, '', content, flags=re.MULTILINE)
            
            # 如果是特定的常见错误变量，进行替换
            if undefined_var == 'now':
                # 不直接替换，而是移除相关行，因为系统没有时间变量
                logger.info("移除了包含now()函数的行，因为系统未定义时间变量")
    
    # 清理可能产生的多余空行
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    content = content.strip()
    
    return content


@router.post("/ai-generate/{task_id}/save", summary="保存AI生成的模板")
async def save_ai_generated_template(
    task_id: str,
    template_name: str,
    session: SessionDep,
    current_user: UserDep,
    template_description: str = ""
):
    """保存AI生成的模板到数据库"""
    
    # 获取AI生成结果
    task_result = task_manager.get_task_status(task_id)
    if not task_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    if task_result.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务尚未完成"
        )
    
    result = task_result.result
    if not result or not result.get("template_content"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有可保存的模板内容"
        )
    
    # 检查模板名称是否已存在
    existing = await session.scalar(
        select(PromptTemplate).where(PromptTemplate.name == template_name)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="模板名称已存在"
        )
    
    # 创建AI生成的模板
    db_template = PromptTemplate(
        name=template_name,
        description=template_description,
        template_content=result["template_content"],
        variables_schema={},  # 可以从模板内容中提取
        output_format={},     # 可以从模板内容中提取
        is_active=result.get("success", False),  # 只有验证成功的模板才能激活
        generation_status=result.get("generation_status", "failed"),
        validation_errors=result.get("validation_errors"),
        ai_generated=True,  # 标记为AI生成
        created_by=current_user.get("username", "admin")
    )
    
    session.add(db_template)
    await session.commit()
    await session.refresh(db_template)
    
    response_data = PromptTemplateResponse.model_validate(db_template)
    return response_data