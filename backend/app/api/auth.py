"""
认证相关API路由
"""
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.core.security import verify_admin_password, create_access_token, get_current_user
from app.schemas.auth import LoginRequest, TokenResponse, UserInfo

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="管理员登录")
async def login(
    login_data: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """管理员登录获取访问令牌"""
    if not await verify_admin_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": "admin"}, expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserInfo, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """获取当前登录用户信息"""
    return UserInfo(username=current_user["username"], role="admin")


@router.post("/logout", summary="登出")
async def logout():
    """登出（客户端应删除令牌）"""
    return {"message": "登出成功"}


@router.get("/menu-config", summary="获取菜单配置")
async def get_menu_config():
    """获取前端菜单配置信息"""
    return settings.get_menu_config()
