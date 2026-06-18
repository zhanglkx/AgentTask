# agent_core

AgentTask 的 Agent 抽象层：把 LangGraph 的 `StateGraph` 包装成一组**模式模板** + **统一运行时**。

## 包含模块

| 模块 | 作用 |
|---|---|
| `state` | `BaseAgentState` + 4 个 pattern 专用 state（TypedDict + Annotated reducer） |
| `events` | 标准化 `AgentEvent`（前后端契约层） |
| `checkpointer` | `get_checkpointer()` 工厂；M2a 仅 MemorySaver，Postgres 留 M3 |
| `interrupt` | HITL `request_interrupt()` / `resume_with()` 包装 |
| `runtime` | `AgentRuntime`：invoke / astream + 错误兜底 + cost 集成 |
| `patterns/react` | ReAct 模式 graph 工厂 |
| `patterns/plan_execute` | Plan-Execute 模式 graph 工厂 |
| `patterns/reflection` | Basic Reflection（写 → critic → revise） |
| `patterns/reflexion` | Reflexion（写 → critic → 经验存储 → 重试） |

## 使用

```python
from langchain_community.chat_models.fake import FakeListChatModel
from agent_core import AgentRuntime, build_react_graph
from tools import get_tool

llm = FakeListChatModel(responses=["…"])
graph = build_react_graph(llm=llm, tools=[get_tool("web_search")])
runtime = AgentRuntime(graph)

result = runtime.invoke({"messages": [("user", "查 LangGraph 是什么")]})
```

详见各子模块 docstring。
