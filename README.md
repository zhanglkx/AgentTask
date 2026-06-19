# AgentTask · 从零基础到 Agent 工程师

> 一个面向**有数年前端经验、零 Python / 零 LLM 经验**的高级工程师，从零学习 Agent 开发并产出生产级作品的渐进式课程仓库。

[![CI](https://github.com/USERNAME/AgentTask/actions/workflows/ci.yml/badge.svg)](https://github.com/USERNAME/AgentTask/actions/workflows/ci.yml)
[![Eval Gate](https://github.com/USERNAME/AgentTask/actions/workflows/eval-gate.yml/badge.svg)](https://github.com/USERNAME/AgentTask/actions/workflows/eval-gate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

> ⚠️ **当前状态：M2a（`packages/tools` + `packages/agent_core` SDK 已交付）**。课程内容（lessons 1-6）将在 M2b 中上线。详见[实施路线图](#实施路线图)。

---

## 这是什么

- ✅ **是**：一份从"零 Python 基础"到"能独立交付生产级 Agent 系统"的完整学习路径，含 16 章渐进式课程 + 9 个生产级 SDK 包 + 一个 Deep Research Agent capstone。
- ✅ **是**：一份大厂级工程化样板（`uv` + `ruff` + `mypy --strict` + `pytest` + `pre-commit` + GitHub Actions + LangSmith + OpenTelemetry + Docker）。
- ✅ **是**：作者的简历项目——证明"我能从零学懂 Agent 开发并产出生产级作品"。

- ❌ **不是**：模型训练 / fine-tuning 教程。
- ❌ **不是**：K8s / Helm / 多环境 CI/CD（属于平台工程师范畴）。
- ❌ **不是**：博客 / 视频教程的代码附件。

## 读者地图

仓库面向三类读者，每类有自己的入口：

| 读者类型 | 推荐路径 |
|---|---|
| 🌱 **零基础学习者** | 根 README → [`docs/prerequisites/python-for-js-devs.md`](./docs/prerequisites/python-for-js-devs.md) → `lessons/01-foundations/`（M2 后上线） |
| 🛠 **中级开发者直接看 SDK 设计** | 根 README → [`docs/architecture.md`](./docs/architecture.md) → `packages/agent_core/`（M2 后上线） |
| 👔 **面试官/HR** | 根 README → capstone 截图 / GIF → `apps/deep_research/`（M5 后上线） → `docs/job-prep.md`（M6 后上线） |

## 课程地图（计划）

| 章节 | 主题 | 状态 |
|---|---|---|
| 01 | LLM 基础 + Python/uv 入门 | ⏳ M2 |
| 02 | Prompting 与结构化输出 | ⏳ M2 |
| 03 | Tool Use 工具调用 | ⏳ M2 |
| 04 | ReAct 模式 | ⏳ M2 |
| 05 | Plan-and-Execute | ⏳ M2 |
| 06 | Reflection / Reflexion | ⏳ M2 |
| 07 | Memory（短期 + 长期） | ⏳ M3 |
| 08 | RAG 基础 | ⏳ M3 |
| 09 | Agentic RAG（Self-RAG / Corrective-RAG） | ⏳ M3 |
| 10 | Multi-Agent: Supervisor | ⏳ M3 |
| 11 | Multi-Agent 拓扑全景 | ⏳ M3 |
| 12 | Streaming 与 HITL | ⏳ M4 |
| 13 | Evaluation 与测试 | ⏳ M4 |
| 14 | Observability 与成本控制 | ⏳ M4 |
| 15 | MCP 与 A2A 协议 | ⏳ M4 |
| 16 | 部署、护栏与代码沙箱 | ⏳ M4 |
| 🚀 | **Capstone: Deep Research Agent** | ⏳ M5 |

## 技术栈一览

| 层 | 用了什么 | 对应 JS 生态 |
|---|---|---|
| 包管理 | `uv` + workspace | `pnpm` + workspace |
| Lint / Format | `ruff` | `eslint` + `prettier` |
| 类型 | `mypy --strict` | `tsc --strict` |
| 测试 | `pytest` + `pytest-asyncio` | `vitest` |
| Hook | `pre-commit` + `commitizen` | `husky` + `lint-staged` |
| 配置 | `pydantic-settings` | `zod` + `dotenv` |
| LLM 框架 | `langgraph` + `langchain` | (无对应) |
| 默认 LLM | DeepSeek（OpenAI 兼容） | - |
| 向量库 | Qdrant + pgvector | - |
| 数据库 | Postgres 16 + Redis 7 | - |
| API | FastAPI + SSE | Express / Hono |
| 前端（capstone） | Next.js 15 + React 19 + Vercel AI SDK | - |
| 容器 | Docker + docker-compose | - |
| CI | GitHub Actions | - |
| 文档 | MkDocs Material | - |

## 快速开始

### 前置要求

- macOS / Linux / Windows + WSL2
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)（一行安装：`curl -LsSf https://astral.sh/uv/install.sh | sh`）
- Docker Desktop（或 Linux 上的 Docker Engine）

### 5 行命令跑通

```bash
git clone https://github.com/USERNAME/AgentTask.git
cd AgentTask
cp .env.example .env  # 填入 DEEPSEEK_API_KEY
make setup            # 装依赖 + 配 hooks
make up               # 起 Postgres + Qdrant + Redis
make test             # 验证安装
```

### 进入 capstone（M5 后可用）

```bash
make capstone-dev     # 启动 FastAPI + Next.js
# 访问 http://localhost:3000
```

## 实施路线图

| 里程碑 | 内容 | 版本号 |
|---|---|---|
| **M0** | 仓库基础设施（当前阶段） | - |
| ✅ M1 | `packages/common` + `packages/llm_providers` | - |
| **M2** | lessons 1–6 + `tools` + `agent_core`（M2a SDK 已交付） | `v0.1.0`(待 M2b) |
| M3 | lessons 7–11 + `memory` + `retrieval` + 多 agent | - |
| **M4** | lessons 12–16 + `tracing` + `evaluation` + `guardrails` + `sandbox` | `v0.2.0` |
| **M5** | Capstone Deep Research Agent | `v1.0.0` |
| M6 | `examples/` + 文档站 + 面试题清单 | - |

详细设计文档：[`docs/superpowers/specs/2026-06-17-agent-task-design.md`](./docs/superpowers/specs/2026-06-17-agent-task-design.md)

## 贡献

参见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## License

[MIT](./LICENSE)
