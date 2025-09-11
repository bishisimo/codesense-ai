"""
审查模板构建器 - 严格按照四个部分构建
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TemplateSection:
    """模板段落"""
    title: str
    content: str
    required: bool = True


class ReviewTemplateBuilder:
    """审查模板构建器 - 严格按照四个部分构建"""
    
    def __init__(self):
        self.sections: List[TemplateSection] = []
    
    def add_output_format_section(self) -> 'ReviewTemplateBuilder':
        """第一部分：输出格式定义（后端固定）"""
        content = """# 输出格式定义

**输出格式要求**:
- 必须严格按照标准JSON格式输出
- 每个维度的评分必须在0-100之间的整数
- level字段必须是以下值之一：low、medium、high、critical
- 每个分类必须提供description字段，说明评分原因和具体扣分项目（详细说明，不超过200字）
- 最终得分通过加权计算得出，确保准确性
- 必须明确说明每个维度的具体扣分项目和扣分原因

**标准JSON输出格式**:
```json
{
    "score": 92,
    "level": "high",
    "summary": "新增代码实现了审查代码的功能，代码质量良好，功能实现正确，如果在命名规范和注释方面进行优化，整体质量会更高。",
    "categories": [
        {
            "name": "代码质量",
            "score": 92,
            "level": "medium", 
            "description": "新增代码整体质量良好，逻辑清晰，功能完整。主要问题：1. 部分变量命名不够规范（如使用temp、data等通用名称），建议使用更具描述性的名称如userInput、responseData；2. 缺少关键注释，特别是复杂逻辑部分。总体评价：代码质量良好，基本功能正确，存在少量改进空间，建议优化命名规范和增加注释。"
        },
        {
            "name": "功能正确性",
            "score": 95,
            "level": "medium",
            "description": "新增功能逻辑基本正确，主要功能实现完整。主要问题：1. 缺少部分边界条件处理，如空值检查、异常处理等；2. 错误处理机制不够完善。总体评价：功能实现正确，但需要加强边界处理和错误处理机制。"
        },
        {
            "name": "性能优化",
            "score": 85,
            "level": "medium",
            "description": "新增代码性能基本可接受，但存在优化空间。主要问题：1. 存在不必要的循环嵌套，可能影响性能；2. 缺少缓存机制，重复计算较多。总体评价：性能基本满足需求，但建议优化算法复杂度和增加缓存机制。"
        }
    ],
    "issues": [
        {
            "id": "naming_convention",
            "type": "warning",
            "severity": "medium",
            "category": "代码质量",
            "title": "变量命名不够规范",
            "description": "第23行使用变量名'temp'过于简单，难以理解其具体用途。在数据处理函数中，变量名应该清晰表达其含义，便于代码维护和理解。",
            "file": "src/example.py",
            "line": 23,
            "suggestion": "将变量名'temp'改为更具描述性的名称。\n\n**当前代码**:\n```python\ntemp = process_data(input_data)\nresult = temp.get_result()\n```\n\n**建议修改为**:\n```python\nprocessed_data = process_data(input_data)\nresult = processed_data.get_result()\n```"
        },
        {
            "id": "boundary_handling",
            "type": "error",
            "severity": "high",
            "category": "功能正确性",
            "title": "缺少边界条件处理",
            "description": "第45行的processData函数缺少对空输入和异常情况的处理。当输入参数为null或undefined时，可能导致程序崩溃或产生意外结果。",
            "file": "src/example.py",
            "line": 45,
            "suggestion": "添加完整的输入验证和异常处理机制。\n\n**当前代码**:\n```python\ndef process_data(data):\n    result = data.get('value')\n    return result * 2\n```\n\n**建议修改为**:\n```python\ndef process_data(data):\n    if not data:\n        raise ValueError(\"输入数据不能为空\")\n    try:\n        value = data.get('value')\n        if value is None:\n            return None\n        return value * 2\n    except (TypeError, AttributeError) as e:\n        raise ValueError(f\"数据处理失败: {str(e)}\")\n```"
        },
        {
            "id": "security_concern",
            "type": "error",
            "severity": "high",
            "category": "安全性",
            "title": "存在SQL注入风险",
            "description": "第89行直接拼接用户输入到SQL查询中，存在SQL注入安全漏洞。恶意用户可能通过构造特殊输入来执行非预期的数据库操作。",
            "file": "src/example.py",
            "line": 89,
            "suggestion": "使用参数化查询防止SQL注入攻击。\n\n**当前代码**:\n```python\nquery = f\"SELECT * FROM users WHERE name = '{user_input}'\"\ncursor.execute(query)\n```\n\n**建议修改为**:\n```python\nquery = \"SELECT * FROM users WHERE name = %s\"\ncursor.execute(query, (user_input,))\n```"
        }
    ]
}
```

---"""
        self.sections.append(TemplateSection("输出格式定义", content, True))
        return self
    
    def add_fixed_review_suggestions(self) -> 'ReviewTemplateBuilder':
        """第二部分：固定审查建议（后端固定）"""
        content = """# 固定审查建议

**审查重点原则**:
⚠️ **重要提醒**: 请专注于当前MR的实际改动，不要将历史代码问题作为评判标准：
- **只审查新增/修改的代码**: 重点关注本次MR中新增、修改或重构的代码部分
- **忽略历史遗留问题**: 对于未改动的历史代码中的命名不规范、缺少注释等问题，不应作为当前MR的扣分项
- **关注改动逻辑**: 重点分析新增代码的逻辑正确性、错误处理、性能影响等

**功能改动分析**:
根据MR标题前缀，请简要描述该MR代码的功能，便于理解代码的业务背景：
- **feat**: 完成了什么功能，新增了哪些特性
- **fix**: 修复了什么问题，解决了哪些bug
- **refactor**: 重构了什么代码，优化了哪些结构
- **chore**: 进行了哪些维护任务，更新了哪些配置

**评分维度(每个维度满分100分)**:
1. 代码质量(权重30%): **仅针对新增/修改代码** - 新增代码是否清晰、易懂，变量和函数命名是否规范，注释是否充足，结构是否合理
2. 功能正确性(权重25%): **仅针对新增/修改代码** - 新增代码逻辑是否正确，边界条件是否处理完成，错误处理机制是否完善
3. 性能优化(权重20%): **仅针对新增/修改代码** - 新增代码的执行效率如何，是否存在潜在的性能瓶颈
4. 安全性(权重15%): **仅针对新增/修改代码** - 新增代码是否需要考虑安全漏洞、数据验证、权限控制
5. 测试覆盖(权重10%): **仅针对新增/修改代码** - 新增代码是否有相应的单元测试、集成测试

**评分标准**:
- **优秀(90-100分)**: 代码质量优秀，逻辑清晰，实现完整，仅有轻微改进空间
- **良好(70-89分)**: 代码质量良好，基本功能正确，存在一些可改进的地方
- **一般(50-69分)**: 代码质量一般，功能基本正确但存在明显问题
- **较差(30-49分)**: 代码质量较差，存在较多问题，需要重构
- **很差(0-29分)**: 代码质量很差，存在严重问题，影响功能或安全

**评分原则**:
- **综合评估**: 根据代码的整体质量进行评分，不要机械地扣分
- **质量层次**: 根据代码的实际质量水平给出相应分数段
- **客观评价**: 好代码给高分，差代码给低分，体现真实的质量差异

**审查示例**:
❌ **错误做法**: "原有函数命名不规范，缺少错误处理" (这是历史问题，不应扣分)
✅ **正确做法**: "新增的登录函数缺少输入验证，建议添加参数校验" (这是当前改动的问题)

---"""
        self.sections.append(TemplateSection("固定审查建议", content, True))
        return self
    
    def add_custom_review_instructions(self, custom_instructions: str) -> 'ReviewTemplateBuilder':
        """第三部分：补充审查建议（自定义）"""
        if not custom_instructions:
            # 如果没有自定义说明，添加默认的审查指导
            content = """
# 补充审查建议

**代码差异分析指导**:
🔍 **请仔细分析代码差异，区分新增代码和历史代码**：
- 重点关注 `+` 标记的新增代码和 `-` 标记的删除代码
- 对于 `+` 新增代码：检查逻辑正确性、错误处理、命名规范、注释完整性
- 对于 `-` 删除代码：判断删除是否合理，是否影响功能完整性
- 对于未标记的代码：这些是历史代码，不应作为当前MR的评判标准

**MR类型具体关注点**:
- **feat (功能开发)**: 新增功能是否完整实现，是否有适当的错误处理和测试
- **fix (问题修复)**: 问题是否被正确识别和修复，是否引入了新的问题
- **refactor (代码重构)**: 重构是否保持了原有功能，代码结构是否更加清晰
- **chore (维护任务)**: 任务是否按预期完成，是否遵循了项目规范

**问题描述和改进建议要求**:
- **具体性**: 必须明确指出问题所在的具体代码行和文件
- **详细性**: 详细说明问题的原因、影响和潜在风险
- **可操作性**: 提供具体的代码示例和改进方案
- **上下文**: 结合代码的实际用途和业务场景进行分析
- **最佳实践**: 引用相关的编程最佳实践和设计模式
- **性能考虑**: 说明改进方案对性能的影响
- **可维护性**: 解释改进如何提高代码的可维护性

**重要**: 请提供客观、专业的审查意见，并给出具体的改进建议。避免将历史代码问题归咎于当前MR。
"""
            self.sections.append(TemplateSection("补充审查建议", content, True))
        else:
            content = f"""# 补充审查建议

{custom_instructions}"""
            self.sections.append(TemplateSection("补充审查建议", content, False))
        return self
    
    def add_project_details_section(self, selected_variables: List[str]) -> 'ReviewTemplateBuilder':
        """第四部分：项目详细（提供模板变量）"""
        content = "# 项目详细\n\n"
        content += "## 项目信息\n"
        
        # 添加项目基本信息
        if "project_name" in selected_variables:
            content += f"- 项目名称: {{{{ project_name }}}}\n"
        if "mr_title" in selected_variables:
            content += f"- 合并请求标题: {{{{ mr_title }}}}\n"
        if "source_branch" in selected_variables:
            content += f"- 源分支: {{{{ source_branch }}}}\n"
        if "target_branch" in selected_variables:
            content += f"- 目标分支: {{{{ target_branch }}}}\n"
        
        content += "\n## 代码变更\n"
        content += "```diff\n{{ code_diff }}\n```\n\n"
        
        content += "---"
        
        self.sections.append(TemplateSection("项目详细", content, True))
        return self
    
    def build_template(self) -> str:
        """构建最终模板"""
        template_parts = []
        for section in self.sections:
            if section.required or section.content.strip():
                template_parts.append(section.content)
        
        return "\n\n".join(template_parts)
    
    def build_standard_template(
        self, 
        selected_variables: List[str] = None, 
        custom_instructions: str = None
    ) -> str:
        """
        构建标准模板 - 严格按照审查定义的四个部分
        
        Args:
            selected_variables: 选择的变量列表
            custom_instructions: 自定义指令
            
        Returns:
            构建的模板字符串
        """
        if selected_variables is None:
            selected_variables = ["project_name", "mr_title", "source_branch", "target_branch"]
        
        return (self
                .add_output_format_section()  # 第一部分：输出格式定义（后端固定）
                .add_fixed_review_suggestions()  # 第二部分：固定审查建议（后端固定）
                .add_custom_review_instructions(custom_instructions)  # 第三部分：补充审查建议（自定义）
                .add_project_details_section(selected_variables)  # 第四部分：项目详细（提供模板变量）
                .build_template())
    
    def get_template_variables_schema(self, selected_variables: List[str] = None) -> List[str]:
        """获取模板使用的变量列表 - 只返回核心变量"""
        if selected_variables is None:
            selected_variables = ["project_name", "mr_title", "source_branch", "target_branch"]
        
        # 只返回已定义的核心变量
        core_variables = ["project_name", "mr_title", "source_branch", "target_branch", "code_diff"]
        return [var for var in selected_variables if var in core_variables]
    
    def get_output_format_schema(self) -> None:
        """输出格式规范由后端统一管理，不需要在数据库中存储"""
        # 输出格式规范是固定的，由 AIResultParser 统一处理
        # 不需要在数据库中重复存储，避免数据冗余和不一致
        return None