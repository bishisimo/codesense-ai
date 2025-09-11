"""
AI审查Prompt模板Schema
"""
from datetime import datetime
from typing import Dict, Optional, List, Union

from pydantic import BaseModel, Field


class PromptTemplateBase(BaseModel):
    """Prompt模板基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    template_content: str = Field(..., min_length=1, description="模板内容")
    variables_schema: Union[List[str], Dict] = Field(..., description="变量定义（列表或字典）")
    # output_format 字段已移除，由后端统一管理
    is_active: bool = Field(True, description="是否激活")


class PromptTemplateCreate(PromptTemplateBase):
    """创建Prompt模板"""
    pass


class PromptTemplateUpdate(BaseModel):
    """更新Prompt模板"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    template_content: Optional[str] = Field(None, min_length=1, description="模板内容")
    variables_schema: Optional[Union[List[str], Dict]] = Field(None, description="变量定义（列表或字典）")
    is_active: Optional[bool] = Field(None, description="是否激活")


class PromptTemplateResponse(BaseModel):
    """Prompt模板响应 - 不包含output_format字段"""
    id: int
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    template_content: str = Field(..., min_length=1, description="模板内容")
    variables_schema: Union[List[str], Dict] = Field(..., description="变量定义（列表或字典）")
    is_active: bool = Field(True, description="是否激活")
    is_default: bool
    created_at: datetime
    updated_at: datetime
    created_by: str

    class Config:
        from_attributes = True


class PromptTemplateListResponse(BaseModel):
    """Prompt模板列表响应"""
    items: List[PromptTemplateResponse]
    total: int
    page: int
    size: int
    pages: int


class TemplateRenderRequest(BaseModel):
    """模板渲染请求"""
    render_data: Dict = Field(..., description="渲染数据")


class TemplateRenderResponse(BaseModel):
    """模板渲染响应"""
    rendered_content: str = Field(..., description="渲染后的内容")
    variables_used: List[str] = Field(..., description="使用的变量列表")
    errors: List[str] = Field(default_factory=list, description="渲染错误")


class TemplateTestRequest(BaseModel):
    """模板测试请求"""
    test_data: Dict = Field(..., description="测试数据")


class TemplateTestResponse(BaseModel):
    """模板测试响应"""
    rendered_prompt: str = Field(..., description="渲染后的prompt")
    validation_result: Dict = Field(..., description="验证结果")
    test_success: bool = Field(..., description="测试是否成功")


class TemplateVariableInfo(BaseModel):
    """模板变量信息"""
    name: str = Field(..., description="变量名")
    description: str = Field(..., description="变量描述")
    type: str = Field(..., description="变量类型")
    required: bool = Field(..., description="是否必需")
    example: Optional[str] = Field(None, description="示例值")
    group: str = Field(..., description="变量分组：core(核心) 或 extended(扩展)")


class TemplateVariablesResponse(BaseModel):
    """模板变量响应"""
    variables: List[TemplateVariableInfo] = Field(..., description="可用变量列表")


class AITemplateGenerationRequest(BaseModel):
    """AI生成模板请求"""
    prompt: str = Field(..., min_length=1, description="生成提示词")
    selected_variables: List[str] = Field(..., min_items=1, description="选中的变量列表")
    template_name: Optional[str] = Field(None, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")


class AITemplateGenerationResponse(BaseModel):
    """AI生成模板响应"""
    template_content: str = Field(..., description="生成的模板内容")
    variables_used: List[str] = Field(..., description="实际使用的变量列表")
    tokens_used: int = Field(..., ge=0, description="消耗的token数量")
    generation_time: int = Field(..., ge=0, description="生成耗时（毫秒）")
