# 多阶段构建Dockerfile - 使用现代化包管理工具
# 使用BuildKit特性进行并行构建优化

# 前端构建阶段 - 使用 bun
FROM oven/bun:1.2-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制 package.json 和 bun.lockb (如果存在)
COPY frontend/package.json ./
COPY frontend/bun.lockb* ./

# 使用 bun 安装依赖 (启用缓存和并行安装)
RUN bun install --frozen-lockfile --cache-dir /tmp/bun-cache

# 复制前端源码 (分离依赖安装和源码复制以利用缓存)
COPY frontend/src/ ./src/
COPY frontend/index.html ./
COPY frontend/vite.config.ts ./
COPY frontend/tsconfig.json ./
COPY frontend/env.config.ts ./
COPY frontend/env.d.ts ./

# 使用 bun 构建 (启用缓存)
RUN bun run build

# 后端运行阶段 - 使用 uv
FROM python:3.13-slim AS backend

# 设置工作目录
WORKDIR /app

# 使用中国镜像源加速
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 安装 uv (现代化的 Python 包管理工具)
RUN pip install -i https://mirrors.ustc.edu.cn/pypi/simple --no-cache-dir uv

# 先复制依赖文件以利用Docker层缓存
COPY backend/pyproject.toml ./
COPY backend/uv.lock ./

# 使用 uv 安装 Python 依赖 (启用并行安装和缓存)
RUN uv pip install --system \
    --index-url https://mirrors.ustc.edu.cn/pypi/simple \
    --no-cache \
    --parallel \
    -e .

# 复制后端源码 (分离依赖安装和源码复制)
COPY backend/ ./backend/

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# 复制配置文件
COPY config.yaml ./config/config.yaml

# 创建非root用户
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8080

# 设置环境变量
ENV PYTHONPATH=/app/backend
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

# 启动命令
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]