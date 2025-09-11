# Code Reviewer Backend Makefile
# 数据库同步和开发工具

.PHONY: help install dev install-dev migrate migrate-create migrate-upgrade migrate-downgrade migrate-history migrate-current db-init db-reset db-drop clean test lint format

# 默认目标
help:
	@echo "Code Reviewer Backend 开发工具"
	@echo ""
	@echo "可用命令:"
	@echo "  install        - 安装生产依赖"
	@echo "  install-dev    - 安装开发依赖"
	@echo "  dev            - 启动开发服务器 (uvicorn)"
	@echo "  start          - 启动后端服务 (自定义脚本)"
	@echo "  start-config   - 使用指定配置文件启动"
	@echo "  start-prod     - 启动生产环境服务"
	@echo "  start-debug    - 启动调试模式"
	@echo "  migrate        - 运行数据库迁移"
	@echo "  migrate-create - 创建新的迁移文件"
	@echo "  migrate-upgrade - 升级到最新版本"
	@echo "  migrate-downgrade - 回滚到上一个版本"
	@echo "  migrate-history - 显示迁移历史"
	@echo "  migrate-current - 显示当前版本"
	@echo "  db-init        - 初始化数据库"
	@echo "  db-reset       - 重置数据库（删除所有表并重新创建）"
	@echo "  db-drop        - 删除数据库"
	@echo "  clean          - 清理缓存和临时文件"
	@echo "  test           - 运行测试"
	@echo "  lint           - 代码检查"
	@echo "  format         - 代码格式化"

# 依赖管理
install:
	@echo "安装生产依赖..."
	uv sync --no-dev

install-dev:
	@echo "安装开发依赖..."
	uv sync

# 开发服务器
dev:
	@echo "启动开发服务器..."
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# 使用自定义启动脚本
start:
	@echo "启动后端服务..."
	uv run python run.py

# 使用指定配置文件启动
start-config:
	@echo "使用指定配置文件启动..."
	@read -p "请输入配置文件路径: " config_path; \
	uv run python run.py --config "$$config_path"

# 生产环境启动
start-prod:
	@echo "启动生产环境服务..."
	uv run python run.py --workers 4 --log-level info

# 调试模式启动
start-debug:
	@echo "启动调试模式..."
	uv run python run.py --debug --reload

# 数据库迁移
migrate: migrate-upgrade

migrate-create:
	@echo "创建新的迁移文件..."
	@read -p "请输入迁移描述: " description; \
	uv run python -m alembic revision --autogenerate -m "$$description"

migrate-upgrade:
	@echo "升级数据库到最新版本..."
	uv run python -m alembic upgrade head

migrate-downgrade:
	@echo "回滚到上一个版本..."
	uv run python -m alembic downgrade -1

migrate-history:
	@echo "显示迁移历史..."
	uv run python -m alembic history --verbose

migrate-current:
	@echo "显示当前数据库版本..."
	uv run python -m alembic current

# 数据库管理
db-init:
	@echo "初始化数据库..."
	uv run python -c "from app.core.database import create_db_and_tables; import asyncio; asyncio.run(create_db_and_tables())"

db-reset:
	@echo "重置数据库..."
	@echo "警告: 这将删除所有数据！"
	@read -p "确认继续? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		uv run alembic downgrade base; \
		uv run alembic upgrade head; \
		echo "数据库已重置"; \
	else \
		echo "操作已取消"; \
	fi

db-drop:
	@echo "删除数据库..."
	@echo "警告: 这将删除数据库中的所有表！"
	@read -p "确认继续? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		uv run alembic downgrade base; \
		echo "数据库表已删除"; \
	else \
		echo "操作已取消"; \
	fi

# 代码质量
clean:
	@echo "清理缓存和临时文件..."
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

test:
	@echo "运行测试..."
	uv run pytest

lint:
	@echo "代码检查..."
	uv run flake8 app/
	uv run mypy app/

format:
	@echo "代码格式化..."
	uv run black app/
	uv run isort app/

# 快速设置（新环境）
setup: install-dev db-init migrate
	@echo "环境设置完成！"
	@echo "运行 'make dev' 启动开发服务器"
