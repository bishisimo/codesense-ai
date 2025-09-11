"""
AI提示词优化服务
"""
from typing import Dict, Any, List
from app.services.ai.ai_service import AIService
from app.core.logging import get_logger

logger = get_logger("ai_prompt_optimizer")


class PromptOptimizerService:
    """AI提示词优化服务"""
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
    
    async def optimize_prompt(
        self,
        original_prompt: str,
        context: str = "",
        optimization_goals: List[str] = None
    ) -> Dict[str, Any]:
        """优化AI提示词"""
        
        if optimization_goals is None:
            optimization_goals = ["清晰度", "具体性", "完整性"]
        
        goals_text = "、".join(optimization_goals)
        
        optimization_prompt = f"""
请优化以下AI提示词，使其更加{goals_text}：

原始提示词：
{original_prompt}

上下文信息：
{context}

优化目标：
- 提高{goals_text}
- 确保提示词结构清晰
- 添加必要的约束和指导
- 优化语言表达

请提供优化后的提示词：
"""
        
        # 调用AI服务
        result = await self.ai_service.generate_response(
            prompt=optimization_prompt,
            system_prompt="你是一个专业的提示词优化专家，擅长改进AI提示词的质量和效果。",
            temperature=0.5,
            max_tokens=1000
        )
        
        return result
    
    async def analyze_prompt_effectiveness(
        self,
        prompt: str,
        expected_output: str = ""
    ) -> Dict[str, Any]:
        """分析提示词的有效性"""
        
        analysis_prompt = f"""
请分析以下AI提示词的有效性：

提示词：
{prompt}

期望输出（可选）：
{expected_output}

请从以下维度进行分析：
1. 清晰度：提示词是否清晰明确
2. 具体性：是否包含足够的细节
3. 完整性：是否涵盖了所有必要信息
4. 约束性：是否有适当的约束条件
5. 可执行性：AI是否能准确理解并执行

请提供详细的分析报告和改进建议：
"""
        
        # 调用AI服务
        result = await self.ai_service.generate_response(
            prompt=analysis_prompt,
            system_prompt="你是一个专业的提示词分析专家，能够深入分析AI提示词的质量和效果。",
            temperature=0.3,
            max_tokens=1500
        )
        
        return result
