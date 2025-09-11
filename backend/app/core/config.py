"""
应用配置管理
"""
import os
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用设置
    
    配置优先级（从高到低）：
    1. 环境变量
    2. config.yaml 文件
    3. 默认值
    """
    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra="allow",
        env_file=None,  # 不使用.env文件
        env_file_encoding='utf-8'
    )
    
    # 服务器配置
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8080
    DEBUG: bool = False
    RELOAD: bool = False  # 热重载配置，独立于DEBUG
    
    # 数据库配置
    DATABASE_TYPE: str = "mysql"  # mysql, postgresql
    DATABASE_URL: str = "mysql+asyncmy://user:password@localhost/codesense_ai"
    
    # GitLab配置
    GITLAB_URL: str = "https://gitlab.example.com"
    GITLAB_TOKEN: str = ""
    GITLAB_WEBHOOK_SECRET: str = ""
    
    # AI配置
    AI_PROVIDER: str = "deepseek"
    AI_API_KEY: str = ""
    AI_MODEL: str = "deepseek-chat"
    AI_MAX_TOKENS: int = 4000
    AI_TIMEOUT_SECONDS: int = 120  # AI请求超时时间（秒）
    
    # 认证配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ADMIN_PASSWORD: str = "admin123"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # 通知配置
    NOTIFICATIONS_EMAIL_ENABLED: bool = False
    NOTIFICATIONS_EMAIL_SMTP_SERVER: str = ""
    NOTIFICATIONS_EMAIL_SMTP_PORT: int = 587
    NOTIFICATIONS_EMAIL_USERNAME: str = ""
    NOTIFICATIONS_EMAIL_PASSWORD: str = ""
    
    NOTIFICATIONS_GITLAB_COMMENT_ENABLED: bool = True
    
    NOTIFICATIONS_FEISHU_ENABLED: bool = False
    NOTIFICATIONS_FEISHU_WEBHOOK_URL: str = ""
    
    # 审查配置
    REVIEW_SCORE_EXCELLENT: int = 80
    REVIEW_SCORE_GOOD: int = 60
    REVIEW_SCORE_POOR: int = 0
    
    # 菜单配置
    MENU_DASHBOARD: bool = True
    MENU_MERGE_REQUESTS: bool = True
    MENU_STATISTICS: bool = False
    MENU_PROMPT_TEMPLATES: bool = False
    
    def __init__(self, **kwargs):
        # 加载YAML配置文件
        yaml_config = self._load_yaml_config()
        
        # 过滤掉YAML中的空字符串值，让环境变量能够覆盖
        # 同时检查是否有对应的环境变量，如果有则跳过YAML中的值
        filtered_yaml_config = {}
        for key, value in yaml_config.items():
            # 检查是否有对应的环境变量
            if os.getenv(key) is not None:
                # 如果有环境变量，跳过YAML中的值
                continue
            elif value != "" and value is not None:
                filtered_yaml_config[key] = value
        
        # 合并配置：过滤后的YAML配置 + 传入的参数
        # pydantic-settings会自动处理环境变量覆盖
        merged_config = {**filtered_yaml_config, **kwargs}
        
        super().__init__(**merged_config)
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """加载YAML配置文件"""
        # 优先使用环境变量指定的配置文件路径
        custom_config_path = os.getenv('CONFIG_PATH')
        if custom_config_path:
            config_paths = [custom_config_path]
        else:
            config_paths = [
                "config/config.yaml",        # backend目录下的配置（优先）
                "../config/config.yaml",     # 项目根目录下的配置（兼容）
                "config.yaml",               # 当前目录下的配置
                "/app/config/config.yaml"    # Docker环境路径
            ]
        
        for config_path in config_paths:
            if Path(config_path).exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        yaml_data = yaml.safe_load(f)
                    
                    # 将嵌套的YAML结构扁平化
                    return self._flatten_yaml_config(yaml_data)
                    
                except Exception as e:
                    # 使用简单的print，因为此时日志系统可能还没初始化
                    print(f"Warning: Failed to load config from {config_path}: {e}")
                    continue
        
        return {}
    
    def _flatten_yaml_config(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """将嵌套的YAML配置扁平化"""
        result = {}
        
        for key, value in data.items():
            if prefix:
                full_key = f"{prefix}_{key}".upper()
            else:
                full_key = key.upper()
            
            if isinstance(value, dict):
                result.update(self._flatten_yaml_config(value, full_key))
            elif isinstance(value, list):
                # 处理列表类型（如CORS_ORIGINS）
                result[full_key] = value
            else:
                result[full_key] = value
        
        # 修复字段名映射
        field_mapping = {
            'AUTH_ADMIN_PASSWORD': 'ADMIN_PASSWORD',
            'AUTH_SECRET_KEY': 'SECRET_KEY',
            'AUTH_ACCESS_TOKEN_EXPIRE_MINUTES': 'ACCESS_TOKEN_EXPIRE_MINUTES',
            'SERVER_DEBUG': 'DEBUG',
        }
        
        # 应用字段名映射
        mapped_result = {}
        for key, value in result.items():
            if key in field_mapping:
                mapped_result[field_mapping[key]] = value
            else:
                mapped_result[key] = value
        
        return mapped_result
    
    def get_menu_config(self) -> Dict[str, bool]:
        """获取菜单配置"""
        return {
            "dashboard": self.MENU_DASHBOARD,
            "merge_requests": self.MENU_MERGE_REQUESTS,
            "statistics": self.MENU_STATISTICS,
            "prompt_templates": self.MENU_PROMPT_TEMPLATES
        }


# 创建全局设置实例
settings = Settings()


def get_database_url() -> str:
    """获取数据库URL"""
    if settings.DATABASE_TYPE.lower() == "mysql":
        return settings.DATABASE_URL or "mysql+asyncmy://user:password@localhost/codesense_ai"
    elif settings.DATABASE_TYPE.lower() == "postgresql":
        return settings.DATABASE_URL or "postgresql+asyncpg://user:password@localhost/codesense_ai"
    else:
        raise ValueError(f"Unsupported database type: {settings.DATABASE_TYPE}. Supported types: mysql, postgresql")
