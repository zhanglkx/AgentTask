# AgentTask 设计文档

> 一个面向"零 Python / 零 LLM 经验、有数年前端经验"的高级工程师，从零学习 Agent 开发并产出生产级作品的渐进式课程仓库。

- **创建日期**: 2026-06-17
- **作者**: AgentTask Author
- **状态**: Approved（待 writing-plans 落地实施计划）

---

## 1. 项目目标

构建一个**渐进式课程 + 生产级核心库 + Capstone 综合产品**三合一的代码仓库，使一名零 Python / 零 LLM 经验的高级前端工程师，能够通过该仓库系统学习当下（2025–2026）主流 Agent 开发模式与工程化实践，并最终产出一个可挂到简历、足以进入头部大厂 Agent 工程师岗位面试环节的作品。

### 1.1 三个并行目标

1. **教学全景**：覆盖 ReAct / Plan-and-Execute / Reflection / Reflexion / Multi-Agent 拓扑 / Memory / RAG / Agentic RAG / Streaming / HITL / Evaluation / Observability / MCP / A2A / Guardrails / Sandbox / Code Execution 等当下主流 agent 模式。
2. **生产级工程化**：仓库内部的代码分层、命名、配置、测试、CI、可观测性、成本控制对齐头部大厂内部 Agent 平台代码标准。
3. **可交付作品**：产出一个完整的 Deep Research Agent（含 FastAPI 后端 + Next.js / React 前端 + 多 agent 编排），单条命令可启动，可作为简历附带项目展示。

### 1.2 目标读者

主目标读者是仓库作者本人（资深 JS/TS 工程师，零 Python / 零 LLM 经验，目标进入头部大厂 Agent 岗）。仓库同时兼容三类读者：

1. **零基础学习者**：按章节顺序学完 16 章 + capstone。
2. **中级开发者**：直接阅读 `packages/` 学习 Agent 平台 SDK 设计。
3. **面试官**：通过 README、capstone 截图、`docs/job-prep.md` 快速评估候选人能力。

### 1.3 非目标

- 不做模型训练 / fine-tuning。
- 不做 K8s / Helm / 多环境 CI/CD / A/B 测试 / Feature flag / Load testing 等"工程化旗舰档"内容（属于平台/SRE 范畴，对 agent 工程师岗的边际收益低）。
- 不深入 Computer Use 类需要操作真实桌面环境的 agent（API 不稳、工程量大）。
- 不做面向博主/教育者的视频或公众号配套内容。

---

## 2. 关键决策汇总

| 维度 | 决策 |
|---|---|
| 项目形态 | 双层结构：渐进式课程 + 生产级核心库（packages） + Capstone 产品（apps） |
| 内容广度 | 全景版（16 章左右） |
| Capstone | Deep Research Agent（带 React 前端） |
| LLM 默认供应商 | DeepSeek（OpenAI 兼容协议接入），保留多供应商抽象，可一键切换至 Claude / OpenAI / Ollama |
| Python 入门 | `docs/prerequisites/python-for-js-devs.md` 速查文档 + 主线章节嵌入式讲解 |
| Python 工具链 | `uv`（包管理 + workspace） |
| 工程化深度 | 进阶档：完整可观测性 + Eval 框架 + Docker + FastAPI + 配置管理 + Secrets + 成本追踪 |
| 教学呈现 | 前期 `.ipynb` notebook 为主；后期 `.py` 模块为主；capstone 完全工程化 |
| 外部依赖 | 生产级：Tavily（搜索）+ Qdrant（向量）+ Postgres + Redis，`docker-compose` 一键起 |
| 前端技术栈 | Next.js 15 + React 19 + TypeScript + Tailwind v4 + shadcn/ui + Vercel AI SDK + reactflow + react-markdown + shiki |
| 文档语言 | 中文（README / 章节文档 / 注释 / Commit message 全部使用中文） |
| 节奏规划 | 不在仓库内规划进度（不写学习路线图） |
| License | MIT |
| Eval Gate | 默认对每个 PR 都跑（带响应缓存 + 小数据集 + `[skip eval]` 标签机制对冲成本） |
| Release 节奏 | M2 完成时打 `v0.1.0`、M4 完成时打 `v0.2.0`、M5 完成时打 `v1.0.0` |

---

## 3. 仓库整体架构

### 3.1 顶层目录结构

```
AgentTask/
├── README.md                        # 项目总览、读者地图、快速开始、章节索引
├── pyproject.toml                   # uv 工作区配置（monorepo root）
├── uv.lock                          # 依赖锁文件（对应 pnpm-lock.yaml）
├── .python-version                  # 固定 Python 3.12
├── .env.example                     # 环境变量模板
├── .gitignore / .dockerignore
├── ruff.toml                        # lint + format 配置
├── mypy.ini                         # 类型检查配置
├── .pre-commit-config.yaml          # 提交前钩子
├── docker-compose.yml               # 一键起 Postgres + Qdrant + Redis + 可选 SigNoz
├── Makefile                         # 命令统一入口
├── LICENSE                          # MIT
├── CHANGELOG.md                     # 由 commitizen 自动生成
├── CONTRIBUTING.md                  # 贡献指南
├── SECURITY.md                      # 安全策略
│
├── docs/
│   ├── prerequisites/
│   │   └── python-for-js-devs.md    # JS/TS ↔ Python 速查对照表
│   ├── architecture.md              # 仓库总体架构图（mermaid）+ 设计决策记录
│   ├── concepts/                    # 跨章节核心概念词典
│   ├── job-prep.md                  # 阶段 6 产出：每章对应的高频面试题
│   └── superpowers/specs/           # 本设计文档 + 未来 spec
│
├── packages/                        # 生产级可复用核心库（uv workspace 子包）
│   ├── common/                      # 配置、日志、错误、重试、成本、缓存
│   ├── llm_providers/               # 多供应商抽象层
│   ├── tools/                       # 工具注册表 + 内置工具
│   ├── memory/                      # 短期/长期记忆
│   ├── retrieval/                   # RAG 组件
│   ├── tracing/                     # OpenTelemetry + LangSmith
│   ├── evaluation/                  # eval 框架 + LLM-as-judge
│   ├── guardrails/                  # 输入/输出安全护栏
│   ├── sandbox/                     # 代码执行沙箱（E2B + Docker fallback）
│   └── agent_core/                  # Agent 抽象、状态、运行时、模式模板
│
├── lessons/                         # 16 章渐进式课程
│   ├── 01-foundations/
│   ├── 02-prompting-and-structured-output/
│   ├── 03-tool-use/
│   ├── 04-react/
│   ├── 05-plan-and-execute/
│   ├── 06-reflection-and-reflexion/
│   ├── 07-memory/
│   ├── 08-rag-basics/
│   ├── 09-agentic-rag/
│   ├── 10-multi-agent-supervisor/
│   ├── 11-multi-agent-topologies/
│   ├── 12-streaming-and-hitl/
│   ├── 13-evaluation-and-testing/
│   ├── 14-observability-and-cost/
│   ├── 15-mcp-and-a2a/
│   └── 16-deployment-guardrails-and-sandbox/
│
├── apps/
│   └── deep_research/               # Capstone: Deep Research Agent
│       ├── api/                     # FastAPI 后端
│       ├── agent/                   # 基于 packages/* 的 agent 编排
│       ├── web/                     # Next.js + React 前端
│       ├── tests/
│       ├── Dockerfile.api
│       ├── Dockerfile.web
│       ├── docker-compose.yml
│       └── README.md
│
├── examples/                        # 短小独立示例
│   ├── browser-use-mini/
│   └── voice-agent-mini/
│
├── scripts/                         # 运维 / 开发脚本（init_db / migrate / eval-run）
│
└── .github/
    ├── pull_request_template.md
    └── workflows/
        ├── ci.yml
        ├── eval-gate.yml
        └── release.yml
```

### 3.2 核心设计原则

1. **`packages/` 与 `lessons/` 的关系**：第 1–6 章的代码独立编写、不依赖 `packages/`，专注讲清楚每个模式的本质；第 7 章起每章会"对比手写实现 vs `packages/` 实现"，让学习者亲眼看到生产级抽象的演化路径。
2. **`uv` workspace**：用 `uv` monorepo workspace 把 `packages/*` 和 `apps/*` 串起来（对应 `pnpm workspace`），改一处自动联动。
3. **每个 lesson 标准结构**：
   ```
   lessons/0X-name/
   ├── README.md            # 中文讲解（原理 + 类比 + 大厂应用场景）
   ├── notebook.ipynb       # 交互式探索（前期占主导）
   ├── src/                 # 可运行的 .py 代码（后期占主导）
   ├── tests/               # 该章配套测试
   ├── exercises/           # 练习题
   ├── solutions/           # 练习答案
   └── NOTES.md             # 章节小结 + 进阶阅读
   ```
4. **Capstone = packages 的活样本**：`apps/deep_research/` 完全基于 `packages/*` 构建，是"看完课程能产出什么"的展示，也是简历的核心作品。

---

## 4. `packages/` 内部模块划分

### 4.1 包依赖图（防止循环依赖）

```
common  ← 所有人都依赖
  ↑
  ├── llm_providers
  ├── tools
  ├── tracing
  ├── memory ──── retrieval
  ├── evaluation
  ├── guardrails
  ├── sandbox
  └── agent_core ← 依赖以上所有
       ↑
       apps/deep_research
       lessons/07+（部分章节）
```

`packages/` 单向依赖，不依赖 `lessons/` / `apps/`。每个包都拥有自己的 `tests/`、`pyproject.toml`、独立可发布。

### 4.2 各包职责

#### `packages/common/` —— 基础设施
- `config.py`：`pydantic-settings` 多环境配置（dev/staging/prod），从 `.env` + 环境变量加载，类型安全。
- `logging.py`：`structlog` 结构化日志，JSON 格式，自动注入 `trace_id` / `agent_name`。
- `errors.py`：统一错误类层级（`AgentError` → `ToolError` / `LLMError` / `RetryableError` ...）。
- `retry.py`：`tenacity` 封装的重试策略（指数退避 + jitter，按错误类型差异化）。
- `cost.py`：成本追踪器（按调用记录 input/output token + 当前价格 → 累计成本）。
- `cache.py`：Redis 客户端封装，提供 LLM 响应缓存装饰器。

#### `packages/llm_providers/` —— 多供应商 LLM 抽象
- `factory.py`：`get_chat_model(provider, model, **kwargs)` 工厂；默认 provider 由配置决定。
- `providers/deepseek.py`：通过 `langchain-openai` 的 `ChatOpenAI` 设置 `base_url=https://api.deepseek.com`。
- `providers/anthropic.py` / `providers/openai.py` / `providers/ollama.py`：各自基于对应 LangChain 集成。
- `middleware.py`：包装任意 chat model：自动成本记录、重试、tracing、可选 Redis 缓存。
- `embeddings.py`：embedding 工厂。

#### `packages/tools/`
- `registry.py`：装饰器 `@tool` 自动注册，含 schema / 权限 / 超时 / 重试策略。
- `base.py`：`Tool` 抽象基类（输入/输出 Pydantic 模型、`run()` / `arun()`）。
- `builtin/`：`web_search.py`（Tavily）/ `web_scrape.py`（trafilatura + readability）/ `python_repl.py` / `file_io.py` / `shell.py`（白名单）/ `vector_search.py` / `sql_query.py`。
- `mcp_adapter.py`：把 MCP server 暴露的工具自动接入工具注册表。

#### `packages/agent_core/` —— Agent 抽象与运行时
- `state.py`：`BaseAgentState` + 各 pattern 专用 state（`ReActState` / `PlanExecuteState` / `ResearchState` ...），用 `TypedDict` + `Annotated[T, reducer]`。
- `runtime.py`：`AgentRuntime` 类，统一处理 streaming / interrupt / checkpoint / 错误兜底。
- `patterns/`：`react.py` / `plan_execute.py` / `reflection.py` / `reflexion.py` / `supervisor.py` / `hierarchical.py` / `swarm.py` / `network.py`。
- `checkpointer.py`：基于 `langgraph-checkpoint-postgres`，开发期内存 saver + 生产期 Postgres saver 自动切换。
- `interrupt.py`：HITL 工具，封装 LangGraph `interrupt()` 原语。
- `events.py`：标准化 agent 事件类型（前端契约层）。

#### `packages/memory/`
- `short_term.py`：消息窗口管理（截断 / 摘要 / token 预算）。
- `long_term.py`：长期记忆，存 Postgres + 向量索引。
- `summary.py`：对话摘要器。
- `episodic.py`：经验记忆（Reflexion 用）。

#### `packages/retrieval/`
- `chunking.py`：fixed / recursive / semantic / structural 多种分块策略。
- `embedding.py`：嵌入模型封装（含批处理、缓存）。
- `vector_store.py`：Qdrant / pgvector 抽象。
- `retriever.py`：dense / hybrid / multi-query / parent-document。
- `reranker.py`：Cohere / BGE-reranker / cross-encoder。
- `query_transform.py`：HyDE / multi-query / step-back。

#### `packages/tracing/`
- `langsmith.py`：LangSmith 配置（一行启用）。
- `otel.py`：OpenTelemetry 配置（导出到本地 Jaeger / SigNoz）。
- `metrics.py`：Prometheus 指标。

#### `packages/evaluation/`
- `dataset.py`：评估数据集管理。
- `metrics/`：faithfulness / answer relevance / context precision / tool selection accuracy。
- `judges.py`：LLM-as-judge 模板。
- `runner.py`：批量执行 eval、生成报告。
- `regression.py`：CI 回归测试 gate。

#### `packages/guardrails/`
- `input_filter.py`：prompt injection 检测、PII 脱敏。
- `output_filter.py`：敏感信息泄漏检查、有害内容过滤。
- `tool_permission.py`：高危工具调用权限校验。

#### `packages/sandbox/`
- `base.py`：`Sandbox` 抽象接口（`execute(code, timeout, resources) -> ExecutionResult`）。
- `e2b_sandbox.py`：E2B 云沙箱实现。
- `docker_sandbox.py`：本地 Docker fallback。
- `policies.py`：网络白名单 / 资源限制 / 超时策略。

---

## 5. 课程大纲（16 章）

### 第 1 章 `01-foundations/` —— LLM 与开发环境基础
- LLM 基础概念（token / temperature / context window / 角色）+ `uv` 工具链 + 第一次调用 DeepSeek + token 计费。
- 产出：`hello_llm.ipynb`（5 个 cell：HTTP → SDK → LangChain → streaming → system prompt）+ `cost_calculator.py`。
- 依赖：无。

### 第 2 章 `02-prompting-and-structured-output/`
- Zero-shot / Few-shot / CoT / Self-Consistency；Pydantic（≈ Zod）；`with_structured_output()`；JSON mode vs function-calling-based structured output；`ChatPromptTemplate` / `MessagesPlaceholder`。
- 产出：`structured_extractor.ipynb`（抽 `Person` / `Company` / `Event`）+ `prompt_template_demo.py`。
- 依赖：`common/config`、`llm_providers/factory`（首次引入 packages）。

### 第 3 章 `03-tool-use/`
- function calling 本质；`@tool` 装饰器；tool schema 自动生成；parallel tool calls；tool error handling；不同模型 tool calling 能力对比。
- 产出：5 个工具 + 手写循环（不用 LangGraph，看清底层）。
- 依赖：开始用 `tools/registry` + `tools/builtin`，并手写一遍对照。

### 第 4 章 `04-react/` —— ReAct 模式
- ReAct 论文核心；LangGraph 入门（`StateGraph` / `add_node` / `add_conditional_edges`）；手写 graph vs `create_react_agent` 预制；停止条件设计。
- 产出：手写 ReAct + prebuilt 两种实现对比。
- 依赖：`agent_core/patterns/react`、`agent_core/state`。

### 第 5 章 `05-plan-and-execute/`
- Plan-and-Execute / ReWOO；planner / executor 双 agent；动态 replan；并行执行；ReAct vs Plan-Execute 选型。
- 产出：研究类任务 plan-execute agent + plan DAG 可视化。
- 依赖：`agent_core/patterns/plan_execute`。

### 第 6 章 `06-reflection-and-reflexion/`
- Basic Reflection / Reflexion / self-consistency / critique-revise；准确率对比基线。
- 产出：写作 agent（写 → critic → 修订）+ coding agent 雏形（写 → 跑测试 → 修订）。
- 依赖：`agent_core/patterns/reflection`、`reflexion`、首次用 `memory/episodic`。

### 第 7 章 `07-memory/` —— 分水岭
- 消息窗口管理；checkpointer 持久化；长期记忆三类型（semantic / episodic / procedural）；profile vs collection；时间衰减与冲突解决。
- 产出：个人助理 agent 跨会话记得偏好；conversation summary chain。
- 依赖：`memory/*` 全套 + `agent_core/checkpointer` (Postgres)。**本章后所有 lesson 默认基于 `packages/` 构建。**

### 第 8 章 `08-rag-basics/`
- embedding 直觉；分块策略；Qdrant 入门 + pgvector 对比；retrieval 评估（recall@k / precision@k）。
- 产出：把仓库 README 索引到 Qdrant，做 RAG demo。
- 依赖：`retrieval/*` 全套。

### 第 9 章 `09-agentic-rag/`
- query rewriting（HyDE / step-back / multi-query）；hybrid search；reranking；Self-RAG；Corrective-RAG；adaptive routing。
- 产出：把第 8 章升级，对比命中率。
- 依赖：`retrieval/reranker`、`retrieval/query_transform`、`agent_core` 编排。

### 第 10 章 `10-multi-agent-supervisor/`
- 多 agent 动机（context 隔离 / 专业化 / 并行）；Supervisor / Router；handoff；shared state；何时不该用多 agent。
- 产出：研究小组（researcher + writer + fact_checker + supervisor）。
- 依赖：`agent_core/patterns/supervisor`。

### 第 11 章 `11-multi-agent-topologies/`
- Hierarchical / Swarm / Network；选型决策树；2026 年主流框架拓扑映射（LangGraph swarm / CrewAI / AutoGen / Google ADK / Microsoft Agent Framework）。
- 产出：同一客服任务三种拓扑实现对比。
- 依赖：`agent_core/patterns/*` 全套。

### 第 12 章 `12-streaming-and-hitl/`
- LangGraph `astream` / `astream_events`；token vs event streaming；FastAPI SSE；Vercel AI SDK；`interrupt()`；resume / time-travel；HITL UX 原则。
- 产出：FastAPI + Next.js 最小 demo（边想边吐字 + 高危工具审批弹窗）。
- 依赖：`agent_core/runtime`、`agent_core/interrupt`、`agent_core/events`。

### 第 13 章 `13-evaluation-and-testing/`
- 单元 / 集成 / eval 区分；`pytest`（≈ vitest）；mock LLM；构建 eval 数据集；LLM-as-judge 偏差缓解；CI eval gate。
- 产出：给前面所有 agent 写完整 eval；GitHub Actions eval-gate workflow。
- 依赖：`evaluation/*` 全套。

### 第 14 章 `14-observability-and-cost/`
- 分布式追踪概念；LangSmith vs OpenTelemetry（Jaeger / SigNoz）双方案；Prometheus 指标；token 成本追踪与归因；prompt caching（Anthropic + DeepSeek context caching）；模型分层路由；语义缓存。
- 产出：capstone 接 LangSmith；Grafana 成本与延迟面板；语义缓存把第 9 章 token 消耗降 60%。
- 依赖：`tracing/*` 全套、`common/cost`、`common/cache`。

### 第 15 章 `15-mcp-and-a2a/`
- MCP（Model Context Protocol）"USB-C for AI tools"；连接现成 MCP server；自己写 MCP server（`mcp` Python SDK）；A2A 协议；MCP vs OpenAPI tool 取舍。
- 产出：capstone 工具暴露为 MCP server 给 Claude Desktop 用；最小 A2A 客户端。
- 依赖：`tools/mcp_adapter`。

### 第 16 章 `16-deployment-guardrails-and-sandbox/`
- Guardrails（prompt injection / PII / 输出过滤 / 工具权限白名单）；Sandbox（E2B + Docker fallback、code-act agent）；部署（多阶段 Dockerfile / docker-compose 全栈 / 配置 / secrets / 健康检查 / 优雅停机 / 蓝绿与金丝雀简介）。
- 产出：capstone 加 guardrails + Dockerfile + 完整 docker-compose；小型 code-act agent。
- 依赖：`guardrails/*`、`sandbox/*`。

### 章节依赖图

```
01 → 02 → 03 → 04
              ├─→ 05 → 06 ─┐
              │             ├─→ 10 → 11 ─┐
              └─→ 07 ─┐    │             │
                       ├──→┘             ├─→ Capstone（增量）
                       08 → 09 ──────────┤
                                          │
              12 ─── 13 ─── 14 ─── 15 ────┤
              16 ───────────────────────────┘
```

---

## 6. Capstone：Deep Research Agent

### 6.1 功能流程

1. 用户输入研究问题（"对比 2026 年主流 agent 框架"）。
2. **Planner agent** 生成研究大纲 → 推送前端 → **HITL 等用户审核 / 编辑大纲**。
3. 用户确认后，**Supervisor** 派发若干 **Researcher agents** 并行抓取（Tavily search + scrape）。
4. 每个 researcher 独立维护自己的 context（隔离 token，避免污染）。
5. **Reflection agent** 检查信息覆盖度，发现缺口 → 触发补充 research。
6. **Writer agent** 生成带引用的 Markdown 报告。
7. **Fact-checker agent** 二次校验关键数据。
8. 全程 streaming 推到前端：plan 流出 → 大纲编辑 UI → 子 agent 执行图（reactflow）实时高亮 → 报告 token 流式渲染 → 引用悬浮预览。
9. 所有 trace 进 LangSmith；成本实时显示在前端 footer。
10. 报告可导出 Markdown / PDF。

### 6.2 架构覆盖

复用第 4 / 5 / 6 / 7 / 9 / 10 / 12 / 13 / 14 / 16 章的全部模式。

### 6.3 技术栈

- **Backend**：FastAPI + LangGraph + Postgres checkpointer + Redis 缓存 + Qdrant 文档库。
- **Frontend**：Next.js 15 + React 19 + TypeScript + Tailwind v4 + shadcn/ui + Vercel AI SDK + reactflow + react-markdown + shiki + TanStack Query。
- **部署**：单条 `docker-compose up` 起全栈（API + Web + Postgres + Qdrant + Redis）。

### 6.4 增量集成策略

从第 10 章起每完成一章新模式就把对应能力增量集成进 capstone，避免最后一次性大集成的复杂度爆炸。`apps/deep_research/web/README.md` 专门讲清楚"前端如何消费 agent 的 streaming 事件"——把 LangGraph 的 `astream_events` 输出转成 Vercel AI SDK 兼容的 SSE 格式。

---

## 7. 开发工作流与质量门

### 7.1 命令统一入口（Makefile）

| 命令 | 作用 |
|---|---|
| `make setup` | 初次安装：装 uv → uv sync → pre-commit install → docker compose up -d → init_db |
| `make up` / `make down` | 起 / 停 docker 服务（Postgres + Qdrant + Redis） |
| `make lint` / `make format` | ruff 检查 / 自动修复 |
| `make type` | mypy 类型检查 |
| `make test` / `make test-fast` | 全量 / 仅快速测试 |
| `make eval` / `make eval-gate` | 跑评估 / CI 评估门 |
| `make notebook` | 启动 Jupyter Lab |
| `make capstone-dev` | 启动 capstone 全栈热重载 |
| `make clean` | 清理缓存 |

### 7.2 工具链

| 工具 | 角色 | JS/TS 对照 |
|---|---|---|
| `ruff` | lint + format | eslint + prettier |
| `mypy --strict` | 静态类型检查 | tsc --strict |
| `pytest` + `pytest-asyncio` + `pytest-cov` | 测试 + 异步 + 覆盖率 | vitest |
| `pre-commit` | git hook 框架 | husky + lint-staged |
| `commitizen` | conventional commits + 自动 changelog | commitizen / cz |

### 7.3 质量策略

- **mypy**：`packages/` + `apps/` 强制 `--strict`；`lessons/` 早期允许宽松、后期 strict。
- **pytest marker**：`fast`（pre-commit）、`integration`（需 docker）、`llm`（真调 LLM，仅 `make eval` 跑）、`slow`。
- **覆盖率门槛**：`packages/` ≥ 80%，`apps/` ≥ 60%，`lessons/` 不强制。

### 7.4 Pre-commit hooks（4 道闸，5 秒内）

1. ruff（lint + format autofix）
2. mypy（仅检查改动的包）
3. pytest -m fast
4. detect-secrets

LLM 真实调用类的测试不在 pre-commit 跑，放 CI 独立 job。

### 7.5 Git 工作流

- **分支**：`main`（保护）+ feature branch（`feat/` / `fix/` / `docs/` / `chore/` / `lesson/0X-name`）。
- **Commit 规范**：Conventional Commits，由 `commitizen` 引导，**全程中文 message**（如 `feat(agent_core): 添加 ReAct 模式 graph 模板`）。
- **PR 模板**：每章一个 PR，含 checklist（README / 测试 / lint+type+test 通过 / LangSmith trace / NOTES.md）。

### 7.6 CI（GitHub Actions）

**`ci.yml`**（每个 PR 必过）：
- Lint + Format check + Type check（~30 秒）
- Unit tests（含 docker 服务，~3 分钟）
- Frontend：`pnpm lint && pnpm typecheck && pnpm build`（~2 分钟）
- 文档构建（mkdocs build，检查死链）

**`eval-gate.yml`**（默认对每个改动 `packages/` 或 `apps/` 的 PR 都跑 + 每周定时）：
- 跑 `make eval-gate`，对比 `main` 基线，下降超 5% 则 fail。
- 通过 PR label `[skip eval]` 显式跳过。
- 对冲成本：小数据集（每章 5–10 用例）+ LLM 响应缓存（按 prompt hash）。

**`release.yml`**（push tag `v*`）：
- 自动 changelog（commitizen）
- 构建 capstone Docker image 推到 GHCR
- 发布 GitHub Release

### 7.7 README 顶部"读者地图"

为三类读者明确入口：① 零基础学习者 → `docs/prerequisites` → `lessons/01`；② 中级开发者 → `docs/architecture.md` → `packages/agent_core/`；③ 面试官 → capstone 截图/GIF → `apps/deep_research/` → `docs/job-prep.md`。

### 7.8 文档体系

- `docs/`：长文档，用 [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) 渲染，GitHub Pages 自动发布。
- 每个 `lessons/0X-*/README.md`：章节正文（中文）。
- 每个 `packages/*/README.md`：包说明（API / 设计决策 / 使用示例）。
- `CHANGELOG.md`：commitizen 自动生成。
- `CONTRIBUTING.md` / `SECURITY.md`：标准社区文档。

### 7.9 IDE / 编辑器

- `.vscode/settings.json` + 推荐扩展（提交到仓库）。
- `.editorconfig`：跨编辑器基础格式。
- `.devcontainer/`：VS Code Dev Container / Codespaces 一键开发环境。

---

## 8. 数据流、状态设计与 LangGraph 编排

### 8.1 State 设计（`packages/agent_core/state.py`）

LangGraph 把 agent 建模成"带共享 state 的有向图"，每个 node 是纯函数 `(state) -> partial_state_update`，与 Redux / Zustand reducer 模型一致。

- 用 `TypedDict`（不用 Pydantic），LangGraph 官方推荐，性能更好，与 reducer 机制契合。
- 每个 reducer 字段都用 `Annotated[T, reducer]` 明示。`messages` 用 `add_messages`，业务字段（如 `evidence`）用自定义去重 reducer。
- State 字段尽量扁平 + 可序列化（pickle 友好），便于 Postgres checkpointer 存储与 time-travel。
- Pydantic 仅用在跨进程 / 跨服务边界（API request/response、tool I/O、长期存储）。

### 8.2 Node 5 条铁律

1. 显式声明依赖（从 `RunnableConfig` 拿 runtime，不用全局变量）。
2. 只读 state 里需要的字段。
3. 调 LLM/工具走 `packages/` 抽象层。
4. 只返回 partial state（让 reducer 合并）。
5. 任何持久化副作用走 `events.emit()` 而非 `print` / 直接 IO。

### 8.3 Graph 编排 4 种典型形态

- **形态 A 线性流**：Plan → Execute → Reflect → End，含条件回边（章节 5、6）。
- **形态 B ReAct 循环**：消息驱动，agent ↔ tools 直到 stop（章节 4、capstone researcher 子 agent）。
- **形态 C Supervisor 分发**：supervisor 路由 → 多 worker 并行 → aggregator（章节 10、11、capstone 研究阶段）。
- **形态 D 分层（subgraph）**：subgraph 与父 graph 不共享 state，通过显式 input/output schema 转换（章节 11、capstone 最终架构）。

### 8.4 Streaming 与事件层

LangGraph `astream_events` 粒度太细，仓库设计自定义事件层（`packages/agent_core/events.py`）：

```python
class AgentEvent(BaseModel):
    event_id: str
    type: Literal[
        "plan.created", "plan.updated",
        "subtask.started", "subtask.progress", "subtask.completed",
        "tool.called", "tool.result",
        "message.delta", "message.completed",
        "interrupt.requested", "interrupt.resolved",
        "cost.update", "trace.link",
        "error", "done",
    ]
    timestamp: datetime
    payload: dict
    trace_id: str
    node: str | None
```

`events_to_sse.py` 把 LangGraph raw event stream 转成此语义事件 → SSE → Vercel AI SDK 渲染 → reactflow 实时高亮。这层抽象让前端不需懂 LangGraph 内部，后端可重构 graph 不影响前端契约。

### 8.5 Checkpointer

- **开发期**：`MemorySaver`（快）。
- **生产期**：`PostgresSaver` 持久化所有 state，支持会话恢复 / time-travel / HITL。
- 仓库提供 `get_checkpointer()` 工厂自动按环境切换。

### 8.6 错误处理 3 层

| 层级 | 范围 | 策略 |
|---|---|---|
| Tool 层 | 单工具失败 | tenacity 重试 + 指数退避；超限把错误作为 observation 喂回 LLM |
| Node 层 | node 异常（限流 / 超时） | LangGraph node-level retry policy + fallback model |
| Graph 层 | agent 整体失败 / 用户中止 / 超步数 | 写 `metadata.failure_reason` + 触发 `error` 事件 + 持久化失败状态 |

---

## 9. 实施路线图与里程碑

不绑定时间，以"代码就绪顺序"切分 6 个里程碑，每个独立可验收。

### M0 仓库基础设施
顶层目录、`uv` workspace、Makefile、ruff/mypy/pytest 配置、pre-commit、`.env.example`、`docker-compose.yml`、CI 三个 workflow 框架（先空跑）、根 README 草稿、LICENSE、`.devcontainer/`、IDE 配置、`docs/prerequisites/python-for-js-devs.md`。
**验收**：clone → `make setup` → `make up` 一切就绪；空 PR 让 CI 三个 workflow 跑过。

### M1 `packages/common` + `packages/llm_providers`
- common：config / logging / errors / retry / cost / cache。
- llm_providers：factory + 4 种 provider + middleware + embeddings。
- 单元测试 + 80% 覆盖率。
**验收**：5 行 demo 调 DeepSeek 然后切换 Ollama 不改业务代码；成本自动记录；限流自动重试。

### M2 lessons 1–6 + `packages/tools` + `packages/agent_core`（→ `v0.1.0`）
- 第 1–6 章完整内容。
- tools（registry + 内置工具）+ agent_core（state / runtime / events / patterns/{react, plan_execute, reflection, reflexion}）。
**验收**：每章独立可运行；`agent_core/patterns/react` 与第 4 章手写版本通过同一道测试题。
**意义**：完成此阶段仓库已具备挂简历资格。

### M3 lessons 7–11 + `packages/memory` + `packages/retrieval` + 多 agent patterns
- 第 7–11 章。
- memory / retrieval / agent_core/patterns/{supervisor, hierarchical, swarm, network} / agent_core/checkpointer (Postgres)。
**验收**：第 7 章 agent 跨会话记得偏好；第 9 章 agentic RAG 比第 8 章 naive RAG 在 10 个测试问题上召回率 +20%；第 11 章三种拓扑跑通同一客服任务。

### M4 lessons 12–16 + `packages/{tracing, evaluation, guardrails, sandbox}`（→ `v0.2.0`）
- 第 12–16 章。
- streaming + HITL + eval 框架 + 可观测性 + MCP/A2A + guardrails + sandbox。
**验收**：CI eval-gate 跑通并对比基线；LangSmith trace 一键打开；MCP server 被 Claude Desktop 识别。
**意义**：完成此阶段 `packages/` 已是大厂级 SDK。

### M5 Capstone Deep Research Agent（→ `v1.0.0`）
- `apps/deep_research/api`（FastAPI）+ `agent`（多 agent 编排）+ `web`（Next.js + React）。
- docker-compose 全栈部署、Dockerfile 多阶段、UX 打磨。
- README 配 GIF / 截图 / 5 个真实研究问题样例。
**验收**：单条 `docker-compose up` 起全栈 → 浏览器输入研究问题 → 完整流式生成报告 → LangSmith trace + 成本面板正常。

### M6（可选） examples + 抛光
- `examples/browser-use-mini/` + `examples/voice-agent-mini/`。
- mkdocs 站点上线 GitHub Pages（可选自定义域名）。
- `docs/job-prep.md`：每章对应高频面试题清单。
**验收**：仓库 polish 到可发 Twitter / 小红书 / 掘金 / Reddit 的程度。

---

## 10. 风险与对冲

| 风险 | 影响 | 对冲措施 |
|---|---|---|
| DeepSeek 在 ReAct / multi-agent 复杂场景下 tool-call 不稳 | lessons 4/10/11 demo 间歇性翻车 | ① README 显式说明各场景准确率；② lesson 提供"模型升级"开关一行切 Claude Sonnet 4.6；③ capstone 关键节点（planner / fact_checker）默认配置可一键升级 |
| LangGraph API 升级（0.6 → 1.0） | 早期章节代码过时 | ① `pyproject.toml` 锁 minor 版本；② lesson README 顶部写 "Tested with langgraph X.Y.Z"；③ dependabot 周更 PR 人工审核合并 |
| DeepSeek API 政策 / 价格变动 | 成本预测与 cache 策略失效 | ① 价格表抽成配置文件；② 同时配好 Anthropic / OpenAI / Ollama 成本配置；③ `make eval-cost-report` 输出预算趋势 |
| eval-gate 每 PR 跑拖慢迭代或吃额度 | 提交成本 | ① 数据集小（每章 5–10）；② LLM 响应缓存（model + prompt hash）；③ `[skip eval]` 标签；④ 每周定时跑作为兜底 |
| 零 Python 基础者卡在第 1–3 章 | 进度受阻 | ① 速查文档先于 lesson 1 产出；② 每章 README 顶部"前端工程师对照"；③ 第 1–3 章 notebook 主导 + 详细 cell 注释 |
| Multi-agent / capstone 复杂度爆炸 | 第 11 章 / capstone 卡住 | ① 严格遵守 5 条 node 铁律；② mermaid + reactflow 可视化；③ capstone 增量集成而非一次性大集成 |
| 国内访问 LangSmith / GitHub Actions 不稳 | 可观测性体验受损 | ① OpenTelemetry + Jaeger / SigNoz 本地自托管替代；② docker-compose 包含可选 SigNoz |
| 前端占用过多精力影响后端进度 | capstone 延期 | ① shadcn/ui 现成组件，不做精美设计；② Vercel AI SDK `useChat` 直接消费 SSE；③ M5 拆成"先后端跑通 + curl"再"前端"两个子里程碑 |

---

## 11. 何时停手

实施过程中**不**追求一次写完所有章节。每个里程碑都是可见可挂的状态——M2 完成时仓库已可挂简历。原则：**质量 > 数量；每章扎实可运行 > 16 章半成品**。如果某章投入产出比低，可以果断砍掉，仓库价值不会因此下降。

---

## 12. 仓库门面（README 顶部章节顺序）

1. 项目定位（1 段：是什么、不是什么、给谁）
2. CI 徽章：lint / type / test / coverage / eval-gate / license
3. 能力概览图（mermaid）：`packages/` ↔ `lessons/` ↔ `apps/` 关系
4. 快速开始（5 行命令跑通 capstone）
5. 课程地图（16 章 + capstone，每章一行 + 进度 emoji）
6. 架构概览（缩略；详见 `docs/architecture.md`）
7. 技术栈一览（表格：用了什么 / 为什么 / 对应 JS 生态）
8. 读者地图（三类读者各自路径）
9. 如何贡献 / 反馈
10. License

---

## 附录 A：完整技术栈清单

### Python 端
- 运行时：Python 3.12
- 包管理：`uv`（含 workspace）
- Lint/Format：`ruff`
- 类型：`mypy --strict`
- 测试：`pytest` + `pytest-asyncio` + `pytest-cov`
- 配置：`pydantic-settings`
- 日志：`structlog`
- 重试：`tenacity`
- HTTP：`httpx`
- LLM 框架：`langgraph` + `langchain` + `langchain-openai` + `langchain-anthropic` + `langchain-community`
- 向量：`qdrant-client` + `pgvector`
- 数据库：`asyncpg` + `langgraph-checkpoint-postgres`
- 缓存：`redis`
- 搜索：`tavily-python`
- 抓取：`trafilatura` + `readability-lxml`
- 沙箱：`e2b` + 本地 Docker
- 评估：`langsmith` + 自建 LLM-as-judge
- 追踪：`opentelemetry-sdk` + `langsmith`
- 指标：`prometheus-client`
- API：`fastapi` + `uvicorn` + `sse-starlette`
- MCP：`mcp` Python SDK

### 前端
- Next.js 15 + React 19 + TypeScript
- Tailwind CSS v4 + shadcn/ui
- TanStack Query
- Vercel AI SDK（`ai` 包，`useChat` / `useObject`）
- reactflow
- react-markdown + shiki

### 基础设施
- Docker + docker-compose
- Postgres 16 + pgvector
- Qdrant
- Redis 7
- 可选：SigNoz / Jaeger（OpenTelemetry 自托管）

### CI / 工具
- GitHub Actions
- pre-commit + commitizen + detect-secrets
- MkDocs Material（文档站）

---

## 附录 B：关键决策记录（ADR 摘要）

| ID | 决策 | 关键理由 |
|---|---|---|
| ADR-001 | 默认 LLM = DeepSeek，但保留 provider 抽象 | 用户已有 DeepSeek key；多供应商抽象本身就是大厂生产形态、简历亮点 |
| ADR-002 | 用 LangGraph 而非自研 agent runtime | 2026 年事实标准；社区 / 文档 / 招聘需求最齐全 |
| ADR-003 | State 用 TypedDict 不用 Pydantic | LangGraph 官方推荐，性能好、reducer 机制契合；Pydantic 留给跨进程边界 |
| ADR-004 | 自定义事件层而非透传 LangGraph 原生事件 | 前后端契约解耦；前端不需懂 LangGraph；后端可重构 graph 不破坏 UI |
| ADR-005 | 工具链用 `uv` 而非 `pip + poetry` | 2025 年下半年起事实主流；性能 10–100x；workspace 完整支持 |
| ADR-006 | eval-gate 默认每 PR 跑 | 用户决策：质量门最严；通过缓存 + 小数据集对冲成本 |
| ADR-007 | 文档语言全中文（含 commit message） | 用户母语思考更深入；不追求海外岗对齐 |
| ADR-008 | Capstone 带 React 前端 | 用户是高级前端，零额外学习成本；Deep Research agent 没 UI 演示效果减半 |
| ADR-009 | `packages/sandbox` 独立成包 | 2026 年 agent 工程师面试 sandbox/code execution 高频考点 |
| ADR-010 | 不做 K8s / Helm / 多环境 CI/CD | 工程化进阶档边界；属于平台工程师范畴，对 agent 工程师边际收益低 |

---

**本设计已确认。下一步交由 writing-plans skill 产出实施计划。**
