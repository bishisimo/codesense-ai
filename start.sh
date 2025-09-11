#!/bin/bash

# GitLab代码审查系统启动脚本

set -e

echo "🚀 启动GitLab代码审查系统..."

# 检查配置文件
if [ ! -f config.yaml ]; then
    echo "❌ 找不到配置文件 config.yaml"
    echo "请检查配置文件是否存在"
    exit 1
fi

echo "📋 配置说明："
echo "   请编辑 config.yaml 文件或设置环境变量来配置系统"
echo "   主要配置项："
echo "   - GitLab URL和Token: 在 gitlab 部分配置"
echo "   - AI API密钥: 在 ai 部分配置"
echo "   - 管理员密码: 在 auth 部分配置"
echo ""
echo "   也可以通过环境变量覆盖配置："
echo "   export GITLAB_TOKEN=your-token"
echo "   export AI_API_KEY=your-key"
echo "   export ADMIN_PASSWORD=your-password"
echo ""

# 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p data logs

# 检查是否使用Docker
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "🐳 使用Docker启动服务..."
    
    echo "使用MySQL数据库..."
    docker-compose up -d
    
    echo ""
    echo "✅ 服务启动完成！"
    echo ""
    echo "📱 访问地址："
    echo "   管理界面: http://localhost:8080"
    echo "   API文档:  http://localhost:8080/docs"
    echo ""
    echo "🔑 默认登录密码: admin123"
    echo "   (可在config.yaml文件中的auth.admin_password修改)"
    echo ""
    echo "📊 查看日志: docker-compose logs -f"
    echo "🛑 停止服务: docker-compose down"
    
else
    echo "❌ 未找到Docker，请安装Docker和docker-compose"
    echo ""
    echo "💡 本地开发启动方式："
    echo "   安装现代化工具:"
    echo "     bun: curl -fsSL https://bun.sh/install | bash"
    echo "     uv:  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "   后端: cd backend && uv pip install -e . && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080"
    echo "   前端: cd frontend && bun install && bun dev"
    echo ""
    echo "   传统方式仍然支持:"
    echo "   后端: cd backend && pip install -e . && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080"
    echo "   前端: cd frontend && npm install && npm run dev"
fi
