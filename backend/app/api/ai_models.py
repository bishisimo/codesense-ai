"""
AI模型和Token使用统计API
"""
from datetime import datetime, timedelta
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.ai_model import AIModel, TokenUsage
from app.schemas.ai_model import (
    AIModelResponse, 
    AIModelCreate, 
    AIModelUpdate,
    TokenUsageResponse,
    TokenUsageStats,
    TokenUsageRequest
)

router = APIRouter()

# 依赖项
SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


@router.get("/models", response_model=List[AIModelResponse], summary="获取AI模型列表")
async def get_ai_models(
    session: SessionDep,
    current_user: UserDep,
    active_only: bool = Query(True, description="只返回启用的模型")
):
    """获取AI模型列表"""
    query = select(AIModel)
    if active_only:
        query = query.where(AIModel.is_active == True)
    
    result = await session.execute(query.order_by(AIModel.provider, AIModel.model_name))
    models = result.scalars().all()
    
    return models


@router.get("/models/{model_id}", response_model=AIModelResponse, summary="获取AI模型详情")
async def get_ai_model(
    session: SessionDep,
    current_user: UserDep,
    model_id: int
):
    """获取AI模型详情"""
    result = await session.execute(select(AIModel).where(AIModel.id == model_id))
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="AI模型不存在")
    
    return model


@router.post("/models", response_model=AIModelResponse, summary="创建AI模型")
async def create_ai_model(
    session: SessionDep,
    current_user: UserDep,
    model_data: AIModelCreate
):
    """创建AI模型"""
    # 检查模型名称是否已存在（全局唯一）
    result = await session.execute(
        select(AIModel).where(AIModel.model_name == model_data.model_name)
    )
    existing_model = result.scalar_one_or_none()
    
    if existing_model:
        raise HTTPException(status_code=400, detail="模型名称已存在，请使用不同的名称")
    
    model = AIModel(**model_data.dict())
    session.add(model)
    await session.commit()
    await session.refresh(model)
    
    return model


@router.put("/models/{model_id}", response_model=AIModelResponse, summary="更新AI模型")
async def update_ai_model(
    session: SessionDep,
    current_user: UserDep,
    model_id: int,
    model_data: AIModelUpdate
):
    """更新AI模型"""
    result = await session.execute(select(AIModel).where(AIModel.id == model_id))
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="AI模型不存在")
    
    # 更新字段
    update_data = model_data.dict(exclude_unset=True)
    
    # 如果更新了模型名称，检查唯一性
    if 'model_name' in update_data and update_data['model_name'] != model.model_name:
        existing_result = await session.execute(
            select(AIModel).where(
                and_(
                    AIModel.model_name == update_data['model_name'],
                    AIModel.id != model_id
                )
            )
        )
        existing_model = existing_result.scalar_one_or_none()
        
        if existing_model:
            raise HTTPException(status_code=400, detail="模型名称已存在，请使用不同的名称")
    
    for field, value in update_data.items():
        setattr(model, field, value)
    
    await session.commit()
    await session.refresh(model)
    
    return model


@router.get("/token-usage", response_model=List[TokenUsageResponse], summary="获取Token使用记录")
async def get_token_usage(
    session: SessionDep,
    current_user: UserDep,
    model_id: Optional[int] = Query(None, description="模型ID筛选"),
    usage_type: Optional[str] = Query(None, description="使用类型筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    limit: int = Query(100, description="返回记录数限制")
):
    """获取Token使用记录"""
    query = select(TokenUsage).join(AIModel)
    
    if model_id:
        query = query.where(TokenUsage.model_id == model_id)
    
    if usage_type:
        query = query.where(TokenUsage.usage_type == usage_type)
    
    if start_date:
        query = query.where(TokenUsage.created_at >= start_date)
    
    if end_date:
        query = query.where(TokenUsage.created_at <= end_date)
    
    result = await session.execute(
        query.order_by(desc(TokenUsage.created_at)).limit(limit)
    )
    usages = result.scalars().all()
    
    return usages


@router.get("/token-usage/stats", response_model=TokenUsageStats, summary="获取Token使用统计")
async def get_token_usage_stats(
    session: SessionDep,
    current_user: UserDep,
    period: str = Query("month", description="统计周期: day, week, month, year"),
    model_id: Optional[int] = Query(None, description="模型ID筛选")
):
    """获取Token使用统计"""
    # 计算时间范围
    now = datetime.utcnow()
    if period == "day":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)
    
    # 构建查询条件
    conditions = [
        TokenUsage.created_at >= start_date
    ]
    
    if model_id:
        conditions.append(TokenUsage.model_id == model_id)
    
    # 总体统计
    total_result = await session.execute(
        select(
            func.count(TokenUsage.id).label('total_requests'),
            func.sum(TokenUsage.total_tokens).label('total_tokens'),
            func.sum(TokenUsage.prompt_tokens).label('total_prompt_tokens'),
            func.sum(TokenUsage.completion_tokens).label('total_completion_tokens'),
            func.sum(TokenUsage.direct_tokens).label('total_direct_tokens'),
            func.sum(TokenUsage.cache_tokens).label('total_cache_tokens'),
            func.sum(TokenUsage.cost).label('total_cost')
        ).where(and_(*conditions))
    )
    total_stats = total_result.first()
    
    # 按模型统计
    model_result = await session.execute(
        select(
            AIModel.provider,
            AIModel.model_name,
            func.count(TokenUsage.id).label('requests'),
            func.sum(TokenUsage.total_tokens).label('tokens'),
            func.sum(TokenUsage.cost).label('cost')
        ).select_from(
            TokenUsage.__table__.join(AIModel.__table__)
        ).where(and_(*conditions))
        .group_by(AIModel.provider, AIModel.model_name)
        .order_by(desc(func.sum(TokenUsage.total_tokens)))
    )
    model_stats = model_result.all()
    
    # 按使用类型统计
    type_result = await session.execute(
        select(
            TokenUsage.usage_type,
            func.count(TokenUsage.id).label('requests'),
            func.sum(TokenUsage.total_tokens).label('tokens'),
            func.sum(TokenUsage.cost).label('cost')
        ).where(and_(*conditions))
        .group_by(TokenUsage.usage_type)
        .order_by(desc(func.sum(TokenUsage.total_tokens)))
    )
    type_stats = type_result.all()
    
    return TokenUsageStats(
        period=period,
        start_date=start_date,
        end_date=now,
        total_requests=total_stats.total_requests or 0,
        total_tokens=total_stats.total_tokens or 0,
        total_prompt_tokens=total_stats.total_prompt_tokens or 0,
        total_completion_tokens=total_stats.total_completion_tokens or 0,
        total_direct_tokens=total_stats.total_direct_tokens or 0,
        total_cache_tokens=total_stats.total_cache_tokens or 0,
        total_cost=float(total_stats.total_cost or 0),
        model_stats=[
            {
                "provider": row.provider,
                "model_name": row.model_name,
                "requests": row.requests,
                "tokens": row.tokens,
                "cost": float(row.cost or 0)
            }
            for row in model_stats
        ],
        type_stats=[
            {
                "usage_type": row.usage_type,
                "requests": row.requests,
                "tokens": row.tokens,
                "cost": float(row.cost or 0)
            }
            for row in type_stats
        ]
    )


@router.post("/token-usage", response_model=TokenUsageResponse, summary="记录Token使用")
async def record_token_usage(
    session: SessionDep,
    current_user: UserDep,
    usage_data: TokenUsageRequest
):
    """记录Token使用"""
    # 验证模型是否存在
    result = await session.execute(select(AIModel).where(AIModel.id == usage_data.model_id))
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="AI模型不存在")
    
    # 创建token使用记录
    token_usage = TokenUsage(**usage_data.dict())
    session.add(token_usage)
    await session.commit()
    await session.refresh(token_usage)
    
    return token_usage
