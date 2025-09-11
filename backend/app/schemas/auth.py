"""
认证相关的Pydantic模式
"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求模式"""
    password: str = Field(..., description="管理员密码")


class TokenResponse(BaseModel):
    """令牌响应模式"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class UserInfo(BaseModel):
    """用户信息模式"""
    username: str = Field(..., description="用户名")
    role: str = Field(default="admin", description="角色")
