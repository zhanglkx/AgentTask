# AgentTask 仓库统一命令入口
# 设计原则: 学习者只需记 6-7 个动词,不用记 uv 长串命令

.PHONY: help setup up down restart logs lint format type test test-fast coverage eval eval-gate notebook capstone-dev clean docs-serve docs-build precommit-all

# 默认目标: 列出所有命令
help:
	@echo "AgentTask 常用命令:"
	@echo ""
	@echo "  make setup          首次安装: 装 uv → uv sync → pre-commit install → docker compose up"
	@echo "  make up             起 docker 服务（Postgres + Qdrant + Redis）"
	@echo "  make down           停 docker 服务"
	@echo "  make restart        重启 docker 服务"
	@echo "  make logs           查看 docker 服务日志"
	@echo ""
	@echo "  make lint           ruff 检查（不修复）"
	@echo "  make format         ruff 自动修复 + format"
	@echo "  make type           mypy 类型检查"
	@echo "  make test           跑全量 pytest（不含 llm 标记）"
	@echo "  make test-fast      只跑 fast 标记的快速测试"
	@echo "  make coverage       跑覆盖率（M1+ 要求 ≥ 80%）"
	@echo "  make precommit-all  在所有文件上跑 pre-commit"
	@echo ""
	@echo "  make eval           跑 evaluation 套件（消耗 LLM 额度）"
	@echo "  make eval-gate      CI 评估门: 跑 eval 并对比基线"
	@echo ""
	@echo "  make notebook       启动 Jupyter Lab"
	@echo "  make capstone-dev   启动 capstone 全栈开发环境"
	@echo ""
	@echo "  make docs-serve     本地预览文档站（mkdocs）"
	@echo "  make docs-build     构建文档站（CI 用）"
	@echo ""
	@echo "  make clean          清理缓存与测试产物"

# ----- 安装与服务 -----

setup:
	@which uv >/dev/null || (echo "请先安装 uv: https://docs.astral.sh/uv/getting-started/installation/" && exit 1)
	uv sync
	uv run pre-commit install --install-hooks
	uv run pre-commit install --hook-type commit-msg
	@echo ""
	@echo "✓ 依赖与 hooks 安装完成"
	@echo "→ 运行 'make up' 启动 docker 服务"
	@echo "→ 运行 'make test' 验证安装"

up:
	docker compose up -d
	@echo "✓ docker 服务已启动"
	@echo "  Postgres: localhost:5432"
	@echo "  Qdrant:   localhost:6333"
	@echo "  Redis:    localhost:6379"

down:
	docker compose down

restart: down up

logs:
	docker compose logs -f --tail=100

# ----- 代码质量 -----

lint:
	uv run ruff check .

format:
	uv run ruff check --fix .
	uv run ruff format .

type:
	uv run mypy .

test:
	uv run pytest -m "not llm"

test-fast:
	uv run pytest -m fast

coverage:
	uv run pytest packages tests --cov=common --cov=llm_providers --cov=tools --cov=agent_core --cov-report=term-missing --cov-fail-under=80

precommit-all:
	uv run pre-commit run --all-files

# ----- 评估 -----

eval:
	@echo "M0 阶段 evaluation 框架尚未实现，此命令将在 M4 后可用"
	@exit 0

eval-gate:
	@echo "M0 阶段 eval-gate 框架尚未实现，此命令将在 M4 后可用"
	@exit 0

# ----- 开发服务 -----

notebook:
	@which jupyter >/dev/null 2>&1 || (echo "请先安装: uv add --dev jupyterlab" && exit 1)
	uv run jupyter lab

capstone-dev:
	@echo "M5 阶段 capstone 尚未实现，此命令将在 M5 后可用"
	@exit 0

# ----- 文档 -----

docs-serve:
	uv run mkdocs serve

docs-build:
	uv run mkdocs build --strict

# ----- 清理 -----

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ipynb_checkpoints -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov coverage.xml site/
	@echo "✓ 缓存已清理（保留 .venv 与 docker volumes）"
