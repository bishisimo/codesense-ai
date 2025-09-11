"""
AI代码审查接口设计 - 专门面向AI场景
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum


class ModelProvider(Enum):
    """AI模型提供商"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"


@dataclass
class ModelConfig:
    """模型配置"""
    provider: ModelProvider
    model_name: str
    api_key: str
    base_url: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: float = 0.3
    timeout: int = 300


@dataclass
class ContextInfo:
    """上下文信息"""
    project_name: str
    mr_title: str
    source_branch: str
    target_branch: str
    commits_count: int = 0
    changes_count: int = 0
    additions_count: int = 0
    deletions_count: int = 0
    commit_sha: Optional[str] = None
    review_type: str = "standard"
    # 增强信息
    complexity_analysis: Optional[Dict[str, Any]] = None
    commit_statistics: Optional[Dict[str, Any]] = None
    diff_info: Optional[Dict[str, Any]] = None
    # 自定义审查指令
    custom_instructions: Optional[str] = None


@dataclass
class PromptTemplate:
    """Prompt模板"""
    name: str
    content: str
    variables_schema: Union[List[str], Dict[str, Any]]
    output_format: Optional[Dict[str, Any]]
    description: Optional[str] = None


@dataclass
class ReviewRequest:
    """审查请求"""
    code_diff: str
    context: ContextInfo
    template: Optional[PromptTemplate] = None
    model_config: Optional[ModelConfig] = None


@dataclass
class ReviewResult:
    """审查结果 - 使用新的标准化格式"""
    score: int
    level: str  # 审查级别: low/medium/high/critical
    summary: str  # 审查总结
    categories: List[Dict[str, Any]]  # 分类评分数组
    issues: List[Dict[str, Any]]  # 发现的问题数组
    tokens_used: int = 0
    direct_token: int = 0  # 非缓存token使用量
    cache_token: int = 0   # 缓存token使用量
    prompt_token: int = 0  # 输入token使用量
    completion_token: int = 0  # 输出token使用量
    model_used: Optional[str] = None
    template_used: Optional[str] = None
    review_content: Optional[str] = None  # Markdown格式的审查报告
    error_message: Optional[str] = None  # 错误信息
    request_duration: Optional[float] = None  # 请求耗时（秒）
    
    # 向后兼容字段（可选）
    score_details: Optional[Dict[str, Any]] = None  # 兼容旧格式
    strengths: Optional[List[str]] = None  # 兼容旧格式
    improvements: Optional[List[str]] = None  # 兼容旧格式


class AIModelInterface(ABC):
    """AI模型接口"""
    
    @abstractmethod
    async def generate_response(self, prompt: str, config: ModelConfig) -> Dict[str, Any]:
        """生成AI响应"""
        pass
    
    @abstractmethod
    def get_provider(self) -> ModelProvider:
        """获取模型提供商"""
        pass
    
    @abstractmethod
    def validate_config(self, config: ModelConfig) -> bool:
        """验证模型配置"""
        pass


class PromptRendererInterface(ABC):
    """Prompt渲染器接口"""
    
    @abstractmethod
    def render_prompt(self, template: PromptTemplate, context: ContextInfo, code_diff: str) -> str:
        """渲染Prompt"""
        pass
    
    @abstractmethod
    def validate_template(self, template: PromptTemplate) -> bool:
        """验证模板"""
        pass
    
    @abstractmethod
    def get_available_variables(self) -> Dict[str, str]:
        """获取可用变量列表"""
        pass


class ContextBuilderInterface(ABC):
    """上下文构建器接口"""
    
    @abstractmethod
    async def build_context(self, merge_request: Any, project: Any, commit_sha: str, review_type: str) -> ContextInfo:
        """构建上下文信息"""
        pass
    
    @abstractmethod
    async def build_enhanced_context(self, context: ContextInfo, git_service: Any) -> ContextInfo:
        """构建增强上下文信息"""
        pass


class ResultParserInterface(ABC):
    """结果解析器接口"""
    
    @abstractmethod
    def parse_response(self, ai_response: str, expected_format: Dict[str, Any]) -> ReviewResult:
        """解析AI响应"""
        pass
    
    @abstractmethod
    def validate_result(self, result: ReviewResult) -> bool:
        """验证解析结果"""
        pass


class AIReviewerInterface(ABC):
    """AI审查器接口 - 专门面向AI场景"""
    
    @abstractmethod
    async def review(self, request: ReviewRequest) -> ReviewResult:
        """执行AI审查"""
        pass
    
    @abstractmethod
    def get_supported_providers(self) -> List[ModelProvider]:
        """获取支持的模型提供商"""
        pass
    
    @abstractmethod
    def get_default_model_config(self) -> ModelConfig:
        """获取默认模型配置"""
        pass


class ModelManagerInterface(ABC):
    """模型管理器接口"""
    
    @abstractmethod
    def register_model(self, provider: ModelProvider, model_interface: AIModelInterface):
        """注册模型"""
        pass
    
    @abstractmethod
    def get_model(self, provider: ModelProvider) -> Optional[AIModelInterface]:
        """获取模型"""
        pass
    
    @abstractmethod
    def list_available_models(self) -> List[ModelProvider]:
        """列出可用模型"""
        pass


class TemplateManagerInterface(ABC):
    """模板管理器接口"""
    
    @abstractmethod
    async def get_template(self, name: str) -> Optional[PromptTemplate]:
        """获取模板"""
        pass
    
    @abstractmethod
    async def get_default_template(self) -> Optional[PromptTemplate]:
        """获取默认模板"""
        pass
    
    @abstractmethod
    async def list_templates(self) -> List[PromptTemplate]:
        """列出模板"""
        pass
    
    @abstractmethod
    async def save_template(self, template: PromptTemplate) -> bool:
        """保存模板"""
        pass
