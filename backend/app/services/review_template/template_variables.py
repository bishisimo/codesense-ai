from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TemplateVariable:
    """模板变量定义"""
    name: str
    description: str
    group: str  # 'core' 或 'extended'
    example: str
    type: str = "string"
    required: bool = False


class TemplateVariables:
    """模板变量集合"""
    
    # 核心变量
    CORE_VARIABLES = [
        TemplateVariable(
            name="code_diff",
            description="代码差异内容",
            group="core",
            example="diff --git a/src/main.py b/src/main.py\nindex 1234567..abcdefg 100644\n--- a/src/main.py\n+++ b/src/main.py\n@@ -10,6 +10,7 @@ def main():\n     print(\"Hello, World!\")\n+    print(\"New feature added!\")\n     return 0",
            required=True
        ),
        TemplateVariable(
            name="project_name",
            description="项目名称",
            group="core",
            example="示例项目",
            required=True
        ),
        TemplateVariable(
            name="mr_title",
            description="合并请求标题",
            group="core",
            example="添加新功能",
            required=True
        ),
        TemplateVariable(
            name="source_branch",
            description="源分支",
            group="core",
            example="feature/new-feature",
            required=True
        ),
        TemplateVariable(
            name="target_branch",
            description="目标分支",
            group="core",
            example="main",
            required=True
        )
    ]
    
    # 扩展变量
    EXTENDED_VARIABLES = [
        TemplateVariable(
            name="commits_count",
            description="提交数量",
            group="extended",
            example="3",
            type="int"
        ),
        TemplateVariable(
            name="changes_count",
            description="变更文件数",
            group="extended",
            example="5",
            type="int"
        ),
        TemplateVariable(
            name="additions_count",
            description="新增行数",
            group="extended",
            example="150",
            type="int"
        ),
        TemplateVariable(
            name="deletions_count",
            description="删除行数",
            group="extended",
            example="20",
            type="int"
        ),
        TemplateVariable(
            name="review_type",
            description="审查类型",
            group="extended",
            example="standard",
            type="string"
        ),
        TemplateVariable(
            name="complexity_analysis",
            description="复杂度分析数据",
            group="extended",
            example="{'complexity_level': 'medium', 'total_lines_changed': 100}",
            type="object"
        ),
        TemplateVariable(
            name="commit_statistics",
            description="提交统计数据",
            group="extended",
            example="{'total_commits': 5, 'most_active_author': '张三'}",
            type="object"
        ),
        TemplateVariable(
            name="diff_info",
            description="差异信息",
            group="extended",
            example="{'total_files': 3, 'total_changes': 100, 'file_types': {'py': 2}}",
            type="object"
        ),

    ]
    

    
    @classmethod
    def get_core_variables(cls) -> List[TemplateVariable]:
        """获取核心变量列表"""
        return cls.CORE_VARIABLES.copy()
    
    @classmethod
    def get_extended_variables(cls) -> List[TemplateVariable]:
        """获取扩展变量列表"""
        return cls.EXTENDED_VARIABLES.copy()
    
    @classmethod
    def get_all_variables(cls) -> List[TemplateVariable]:
        """获取所有变量列表"""
        return cls.CORE_VARIABLES + cls.EXTENDED_VARIABLES
    
    @classmethod
    def get_variables_dict(cls) -> dict:
        """获取变量字典格式 {name: description}"""
        variables_dict = {}
        for var in cls.get_all_variables():
            variables_dict[var.name] = var.description
        return variables_dict
    
    @classmethod
    def get_core_variables_dict(cls) -> dict:
        """获取核心变量字典格式 {name: description}"""
        variables_dict = {}
        for var in cls.get_core_variables():
            variables_dict[var.name] = var.description
        return variables_dict
    
    @classmethod
    def get_extended_variables_dict(cls) -> dict:
        """获取扩展变量字典格式 {name: description}"""
        variables_dict = {}
        for var in cls.get_extended_variables():
            variables_dict[var.name] = var.description
        return variables_dict

    @classmethod
    def get_variables_by_group(cls, group: str) -> List[TemplateVariable]:
        """根据分组获取变量"""
        if group == "core":
            return cls.get_core_variables()
        elif group == "extended":
            return cls.get_extended_variables()
        else:
            return []

    @classmethod
    def get_required_variables(cls) -> List[TemplateVariable]:
        """获取必需变量列表"""
        return [var for var in cls.get_all_variables() if var.required]

    @classmethod
    def get_variable_info(cls, name: str) -> Optional[TemplateVariable]:
        """根据名称获取变量信息"""
        for var in cls.get_all_variables():
            if var.name == name:
                return var
        return None
    
    @classmethod
    def get_example_data(cls) -> dict:
        """获取所有变量的示例数据，用于模板验证和测试"""
        import ast
        
        example_data = {}
        
        for var in cls.get_all_variables():
            try:
                if var.type == "int":
                    example_data[var.name] = int(var.example)
                elif var.type == "object":
                    # 尝试解析字符串为字典
                    example_data[var.name] = ast.literal_eval(var.example)
                else:
                    # 默认为字符串类型
                    example_data[var.name] = var.example
            except (ValueError, SyntaxError):
                # 如果解析失败，使用原始字符串
                example_data[var.name] = var.example
        
        return example_data
