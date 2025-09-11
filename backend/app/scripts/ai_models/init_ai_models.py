#!/usr/bin/env python3
"""
初始化AI模型数据
"""
import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from app.core.database import get_session
from app.models.ai_model import AIModel
from app.libs.ai_models import list_models


async def init_ai_models():
    """初始化AI模型数据"""
    async for session in get_session():
        try:
            # 检查是否已有数据
            result = await session.execute(select(AIModel))
            existing_models = result.scalars().all()
            
            if existing_models:
                print(f"已存在 {len(existing_models)} 个AI模型，将更新为新版本配置")
                
                # 更新现有记录而不是删除重建
                model_definitions = list_models(active_only=False)
                
                for i, model_def in enumerate(model_definitions):
                    # 查找对应的现有模型记录（按模型名称匹配，而不是ID）
                    existing_model = None
                    for existing in existing_models:
                        if existing.model_name == model_def.name and existing.provider == model_def.provider:
                            existing_model = existing
                            break
                    
                    if existing_model:
                        # 更新现有记录
                        existing_model.provider = model_def.provider
                        existing_model.base_url = model_def.base_url
                        existing_model.model_name = model_def.name
                        existing_model.display_name = model_def.display_name
                        existing_model.model_type = model_def.model_type
                        existing_model.version = model_def.version
                        existing_model.description = model_def.description
                        existing_model.capabilities = model_def.capabilities.__dict__ if model_def.capabilities else None
                        existing_model.pricing = model_def.pricing.__dict__ if model_def.pricing else None
                        existing_model.is_active = model_def.is_active
                        existing_model.is_default = model_def.is_default
                        print(f"更新模型: {model_def.provider}/{model_def.name} (定义ID: {model_def.id})")
                    else:
                        # 创建新记录
                        model = AIModel(
                            provider=model_def.provider,
                            base_url=model_def.base_url,
                            model_name=model_def.name,
                            display_name=model_def.display_name,
                            model_type=model_def.model_type,
                            version=model_def.version,
                            description=model_def.description,
                            capabilities=model_def.capabilities.__dict__ if model_def.capabilities else None,
                            pricing=model_def.pricing.__dict__ if model_def.pricing else None,
                            is_active=model_def.is_active,
                            is_default=model_def.is_default
                        )
                        session.add(model)
                        print(f"创建模型: {model_def.provider}/{model_def.name} (定义ID: {model_def.id})")
            else:
                # 从新的模型定义创建AI模型
                model_definitions = list_models(active_only=False)
                models = []
                
                for i, model_def in enumerate(model_definitions):
                    model = AIModel(
                        provider=model_def.provider,
                        base_url=model_def.base_url,
                        model_name=model_def.name,
                        display_name=model_def.display_name,
                        model_type=model_def.model_type,
                        version=model_def.version,
                        description=model_def.description,
                        capabilities=model_def.capabilities.__dict__ if model_def.capabilities else None,
                        pricing=model_def.pricing.__dict__ if model_def.pricing else None,
                        is_active=model_def.is_active,
                        is_default=model_def.is_default
                    )
                    models.append(model)
                    print(f"创建模型: {model_def.provider}/{model_def.name} (定义ID: {model_def.id})")
                
                # 批量插入
                session.add_all(models)
            await session.commit()
            
            # 重新查询以获取最终结果
            result = await session.execute(select(AIModel))
            final_models = result.scalars().all()
            print(f"成功初始化 {len(final_models)} 个AI模型:")
            for model in final_models:
                print(f"  - {model.provider}/{model.model_name}: {model.display_name}")
                
        except Exception as e:
            print(f"初始化AI模型失败: {e}")
            await session.rollback()
        finally:
            await session.close()
        break


if __name__ == "__main__":
    asyncio.run(init_ai_models())
