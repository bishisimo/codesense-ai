"""
AI模板生成器服务 - 重新设计版本
"""
from typing import List, Dict, Any, Optional, Tuple
from app.services.review_template.template_variables import TemplateVariables
from app.core.logging import get_logger
import re

logger = get_logger("ai_template_generator")


class TemplateGeneratorService:
    """AI模板生成器服务 - 重新设计版本"""
    
    def __init__(self, ai_service):
        self.ai_service = ai_service
        self.template_variables = TemplateVariables()
    
    async def generate_template(
        self,
        prompt: str,
        selected_variables: List[str],
        template_name: str = None,
        description: str = None,
        template_type: str = "standard"
    ) -> Dict[str, Any]:
        """生成AI模板 - 重新设计版本"""
        
        try:
            # 验证选择的变量
            self._validate_selected_variables(selected_variables)
            
            # 获取变量描述信息
            variables_info = self._build_variables_description(selected_variables)
            
            # 构建AI提示词
            ai_prompt = self._build_prompt(
                prompt, variables_info, template_name, description, template_type
            )
            
            # 调用AI服务
            result = await self.ai_service.generate_response(
                prompt=ai_prompt,
                system_prompt=self._get_system_prompt(template_type),
                temperature=0.5,
                max_tokens=2500
            )
            
            # 获取生成的模板内容
            template_content = result.get("content", "")
            if not template_content:
                raise ValueError("AI未生成模板内容")
            
            # 验证生成的模板
            validation_result = self._validate_generated_template(
                template_content, selected_variables
            )
            
            if not validation_result["is_valid"]:
                return {
                    "success": False,
                    "template_content": template_content,
                    "validation_errors": validation_result["errors"],
                    "generation_status": "failed",
                    "message": "模板生成成功但验证失败"
                }
            
            logger.info(f"模板生成并验证成功，使用变量: {selected_variables}")
            return {
                "success": True,
                "template_content": template_content,
                "validation_errors": [],
                "generation_status": "success",
                "message": "模板生成并验证成功"
            }
                
        except Exception as e:
            logger.error(f"模板生成失败: {str(e)}")
            return {
                "success": False,
                "template_content": "",
                "validation_errors": [str(e)],
                "generation_status": "failed",
                "message": f"模板生成失败: {str(e)}"
            }
    
    def _validate_generated_template(
        self, 
        template_content: str, 
        selected_variables: List[str]
    ) -> Dict[str, Any]:
        """验证生成的模板"""
        errors = []
        
        # 1. 检查是否包含必要的Jinja2语法
        if not re.search(r'\{\{.*?\}\}', template_content):
            errors.append("模板缺少Jinja2变量引用语法")
        
        # 2. 检查是否使用了未授权的变量
        used_variables = self._extract_used_variables(template_content)
        unauthorized_vars = [var for var in used_variables if var not in selected_variables]
        if unauthorized_vars:
            errors.append(f"使用了未授权的变量: {', '.join(unauthorized_vars)}")
        
        # 3. 检查是否使用了禁止的函数
        forbidden_functions = ['now', 'date', 'time', 'strftime', 'random', 'uuid']
        for func in forbidden_functions:
            if re.search(rf'\b{func}\s*\(', template_content, re.IGNORECASE):
                errors.append(f"使用了禁止的函数: {func}")
        
        # 4. 检查代码块是否完整
        code_blocks = re.findall(r'```(\w+)?', template_content)
        if len(code_blocks) % 2 != 0:
            errors.append("代码块标记不完整")
        
        # 5. 检查模板结构是否合理
        if len(template_content.strip()) < 100:
            errors.append("模板内容过短，可能不完整")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "used_variables": used_variables
        }
    
    def _extract_used_variables(self, template_content: str) -> List[str]:
        """提取模板中使用的变量"""
        variable_pattern = r'\{\{\s*(\w+)\s*\}\}'
        matches = re.findall(variable_pattern, template_content)
        return list(set(matches))  # 去重
    
    def _validate_selected_variables(self, selected_variables: List[str]) -> None:
        """验证选择的变量"""
        if not selected_variables:
            raise ValueError("必须选择至少一个变量")
        
        all_variables = self.template_variables.get_all_variables()
        available_vars = {var.name for var in all_variables}
        
        invalid_vars = [var for var in selected_variables if var not in available_vars]
        if invalid_vars:
            raise ValueError(f"无效的变量: {invalid_vars}")
    
    def _build_variables_description(self, selected_variables: List[str]) -> str:
        """构建变量描述信息"""
        all_variables = self.template_variables.get_all_variables()
        
        variable_descriptions = []
        for var in all_variables:
            if var.name in selected_variables:
                description = f"""- {{ {var.name} }}: {var.description}
  - 类型: {var.type}
  - 示例: {var.example}
  - 用途: {self._get_variable_usage(var.name)}"""
                variable_descriptions.append(description)
        
        return "\n".join(variable_descriptions)
    
    def _get_variable_usage(self, variable_name: str) -> str:
        """获取变量的具体用途说明"""
        usage_map = {
            "project_name": "在模板中引用项目信息，如标题、描述等",
            "source_branch": "说明代码来源分支，用于上下文描述",
            "target_branch": "说明代码合并目标，用于对比分析",
            "changes_count": "评估代码变更规模，用于重要性判断",
            "additions_count": "评估新增代码量，用于复杂度分析",
            "deletions_count": "评估删除代码量，用于影响范围分析",
            "files_changed": "了解影响范围，用于风险评估",
            "focus_areas": "指导审查重点，用于定制化审查",
            "author": "了解代码背景，用于质量评估",
            "commits_count": "评估提交频率，用于稳定性分析",
            "mr_title": "了解变更目的，用于业务价值评估"
        }
        return usage_map.get(variable_name, "用于模板中的动态内容展示")
    
    def _build_prompt(
        self,
        prompt: str,
        variables_info: str,
        template_name: str = None,
        description: str = None,
        template_type: str = "standard"
    ) -> str:
        """构建AI提示词"""
        
        template_context = ""
        if template_name:
            template_context += f"模板名称: {template_name}\n"
        if description:
            template_context += f"模板描述: {description}\n"
        
        return f"""
请生成一个专业的Jinja2代码审查报告模板。

## 模板要求
{template_context}
用户需求: {prompt}

## 可用变量
{variables_info}

## 输出格式要求
请生成一个完整的Jinja2模板，必须包含以下部分：

### 1. 审查指令和上下文说明
- 使用项目信息变量提供上下文
- 说明审查范围和重点

### 2. 动态内容生成
- 根据变量值动态生成内容
- 使用条件判断处理可选变量
- 使用循环处理数组类型变量

### 3. 标准JSON输出格式要求
- 明确要求AI返回标准格式
- 包含评分、分类、问题等字段
- 提供具体的字段说明和示例

### 4. 审查指导
- 根据变量内容提供个性化审查建议
- 包含具体的审查维度和标准

## 技术规范
1. 使用Jinja2语法，支持条件判断和循环
2. 只使用指定的变量，严格禁止使用其他变量
3. 使用Markdown格式，结构清晰易读
4. 添加适当的条件判断和循环逻辑
5. 确保模板结构完整，逻辑清晰

## 重要注意事项
- 直接输出模板内容，不要添加任何说明文字
- 不要使用代码块包裹（不要用```jinja或```markdown）
- 不要添加免责声明或额外说明
- 只输出纯净的Jinja2模板内容
- 严格禁止使用未定义的变量（如now()、date()、time()等）
- 不要自行创建或假设任何变量
- 严格禁止使用时间相关函数（如now、date、time、strftime等）
- 只使用提供的变量列表中的变量
- 代码块标记必须完整（如```diff开始必须有```结束）
- 所有变量引用必须使用双大括号格式：{{ variable_name }}

## 模板类型: {template_type}
根据模板类型调整内容重点：
- standard: 标准代码审查，关注质量、安全、性能
- security: 安全审查，重点关注安全漏洞
- performance: 性能审查，重点关注性能优化
- quality: 质量审查，重点关注代码质量
- testing: 测试审查，重点关注测试覆盖

请生成完整的模板内容：
"""
    
    def _get_system_prompt(self, template_type: str) -> str:
        """获取系统提示词"""
        base_prompt = "你是一个专业的代码审查模板生成专家，擅长使用Jinja2语法创建高质量的代码审查报告模板。"
        
        # 添加严格的变量使用限制
        base_prompt += " 你必须严格遵守以下规则："
        base_prompt += " 1. 只使用用户明确选择的变量，绝对不要使用其他变量"
        base_prompt += " 2. 严格禁止使用时间函数（now、date、time、strftime等）"
        base_prompt += " 3. 所有代码块标记必须完整配对"
        base_prompt += " 4. 变量引用必须使用正确的Jinja2语法：{{ variable_name }}"
        
        type_specific = {
            "security": "特别擅长安全审查模板，能够识别各种安全漏洞和风险点。",
            "performance": "特别擅长性能审查模板，能够识别性能瓶颈和优化机会。",
            "quality": "特别擅长代码质量审查模板，能够识别代码规范和最佳实践问题。",
            "testing": "特别擅长测试审查模板，能够识别测试覆盖和质量问题。"
        }
        
        return base_prompt + " " + type_specific.get(template_type, "")
