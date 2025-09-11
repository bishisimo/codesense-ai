"""
统一AI服务层

提供统一的AI模型调用接口，封装所有AI相关的业务逻辑。
"""

import httpx
import arrow
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.logging import get_logger
from app.libs.ai_models import get_model_definition, list_models
from app.services.review.ai_interfaces import ModelConfig, ModelProvider

logger = get_logger("ai_service")


class AIService:
    """统一AI服务"""
    
    def __init__(self):
        self.default_model = self._get_default_model()
    
    def _get_default_model(self):
        """获取默认模型"""
        models = list_models(active_only=True)
        return next((m for m in models if m.is_default), models[0] if models else None)
    
    def get_model_config(self, model_id: Optional[str] = None) -> ModelConfig:
        """获取模型配置"""
        if model_id:
            model_def = get_model_definition(model_id)
            if not model_def:
                raise ValueError(f"Model {model_id} not found")
        else:
            model_def = self.default_model
            if not model_def:
                raise ValueError("No default model found")
        
        # 根据模型定义创建配置
        provider = ModelProvider(model_def.provider.lower())
        
        return ModelConfig(
            provider=provider,
            model_name=model_def.name,
            api_key=settings.AI_API_KEY,
            base_url=model_def.base_url,
            max_tokens=model_def.capabilities.max_tokens if model_def.capabilities else None,
            temperature=0.3,
            timeout=settings.AI_TIMEOUT_SECONDS
        )
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: str = "你是一个专业的AI助手，请根据用户的要求提供帮助。",
        model_id: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """生成AI响应"""
        start_time = arrow.now()
        
        try:
            # 获取模型配置
            model_config = self.get_model_config(model_id)
            
            # 覆盖配置参数
            if temperature != 0.3:
                model_config.temperature = temperature
            if max_tokens:
                model_config.max_tokens = max_tokens
            
            # 构建完整的提示词
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # 调用相应的AI提供商
            if model_config.provider == ModelProvider.DEEPSEEK:
                result = await self._call_deepseek(full_prompt, model_config)
            elif model_config.provider == ModelProvider.OPENAI:
                result = await self._call_openai(full_prompt, model_config)
            elif model_config.provider == ModelProvider.CLAUDE:
                result = await self._call_claude(full_prompt, model_config)
            else:
                raise ValueError(f"Unsupported provider: {model_config.provider}")
            
            # 计算请求耗时
            request_duration = (arrow.now() - start_time).total_seconds()
            result["request_duration"] = request_duration
            
            return result
                
        except Exception as e:
            logger.error(f"AI服务调用失败: {e}")
            raise
    
    async def _call_deepseek(self, prompt: str, config: ModelConfig) -> Dict[str, Any]:
        """调用DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "model": config.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": config.temperature,
            "stream": False
        }

        if config.max_tokens and config.max_tokens > 0:
            payload["max_tokens"] = config.max_tokens

        async with httpx.AsyncClient(timeout=config.timeout) as client:
            try:
                # 使用模型配置中的base_url
                api_url = f"{config.base_url}/chat/completions"
                response = await client.post(
                    api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"DeepSeek API error: {e.response.status_code} - {e.response.text}")
                raise ValueError(f"DeepSeek API 请求失败: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logger.error(f"DeepSeek API request failed: {e}")
                raise

        if not result.get("choices") or len(result["choices"]) == 0:
            raise ValueError("DeepSeek API 返回的响应格式异常：没有找到 choices")

        ai_response = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})
        tokens_used = usage.get("total_tokens", 0)
        
        # 提取缓存相关的token信息
        direct_token = usage.get("prompt_cache_miss_tokens", 0)
        cache_token = usage.get("prompt_cache_hit_tokens", 0)
        
        # 提取输入输出token信息
        prompt_token = usage.get("prompt_tokens", 0)
        completion_token = usage.get("completion_tokens", 0)
        
        logger.info(f"DeepSeek token usage - total: {tokens_used}, direct: {direct_token}, cache: {cache_token}")

        return {
            "content": ai_response,
            "tokens_used": tokens_used,
            "direct_token": direct_token,
            "cache_token": cache_token,
            "prompt_token": prompt_token,
            "completion_token": completion_token,
            "model": config.model_name,
            "provider": config.provider.value
        }
    
    async def _call_openai(self, prompt: str, config: ModelConfig) -> Dict[str, Any]:
        """调用OpenAI API"""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": config.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": config.temperature,
            "stream": False
        }

        if config.max_tokens and config.max_tokens > 0:
            payload["max_tokens"] = config.max_tokens

        base_url = config.base_url or "https://api.openai.com/v1"
        
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            try:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"OpenAI API error: {e.response.status_code} - {e.response.text}")
                raise ValueError(f"OpenAI API 请求失败: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logger.error(f"OpenAI API request failed: {str(e)}")
                raise

        if not result.get("choices") or len(result["choices"]) == 0:
            raise ValueError("OpenAI API 返回的响应格式异常：没有找到 choices")

        ai_response = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})
        tokens_used = usage.get("total_tokens", 0)

        return {
            "content": ai_response,
            "tokens_used": tokens_used,
            "direct_token": tokens_used,  # OpenAI没有缓存token概念
            "cache_token": 0,
            "prompt_token": usage.get("prompt_tokens", 0),
            "completion_token": usage.get("completion_tokens", 0),
            "model": config.model_name,
            "provider": config.provider.value
        }
    
    async def _call_claude(self, prompt: str, config: ModelConfig) -> Dict[str, Any]:
        """调用Claude API"""
        headers = {
            "x-api-key": config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": config.model_name,
            "max_tokens": config.max_tokens or 4000,
            "temperature": config.temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        async with httpx.AsyncClient(timeout=config.timeout) as client:
            try:
                # 使用模型配置中的base_url
                api_url = f"{config.base_url}/messages"
                response = await client.post(
                    api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Claude API error: {e.response.status_code} - {e.response.text}")
                raise ValueError(f"Claude API 请求失败: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logger.error(f"Claude API request failed: {str(e)}")
                raise

        if not result.get("content") or len(result["content"]) == 0:
            raise ValueError("Claude API 返回的响应格式异常：没有找到 content")

        ai_response = result["content"][0]["text"]
        usage = result.get("usage", {})
        tokens_used = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

        return {
            "content": ai_response,
            "tokens_used": tokens_used,
            "direct_token": tokens_used,  # Claude没有缓存token概念
            "cache_token": 0,
            "prompt_token": usage.get("input_tokens", 0),
            "completion_token": usage.get("output_tokens", 0),
            "model": config.model_name,
            "provider": config.provider.value
        }
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        models = list_models(active_only=True)
        return [model.id for model in models]
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """获取模型信息"""
        model_def = get_model_definition(model_id)
        if not model_def:
            return None
        
        return {
            "id": model_def.id,
            "name": model_def.name,
            "display_name": model_def.display_name,
            "provider": model_def.provider,
            "model_type": model_def.model_type,
            "version": model_def.version,
            "description": model_def.description,
            "capabilities": model_def.capabilities.__dict__ if model_def.capabilities else None,
            "pricing": model_def.pricing.__dict__ if model_def.pricing else None,
            "is_active": model_def.is_active,
            "is_default": model_def.is_default
        }


# 全局AI服务实例
ai_service = AIService()
