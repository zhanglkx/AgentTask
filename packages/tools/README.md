# tools

AgentTask 工具层。统一封装 agent 可调用的"动作"。

## 公开 API

```python
from tools import Tool, tool, get_tool, list_tools
from tools.builtin import web_search, web_scrape, python_repl, file_io, shell
```

## 设计

- `Tool` 抽象基类继承 LangChain `BaseTool`，让 LangGraph `tool_calling_agent` 直接消费；同时暴露我们自己的输入/输出 Pydantic schema 与权限策略（`require_approval` / `allow_paths` 等）。
- `@tool` 装饰器把普通函数注册到全局表，自动从函数签名推 input schema。
- 5 个内置工具按"web / system"分两大类，分别有依赖（Tavily key / 路径白名单 / 命令白名单）。
- 错误统一抛 `common.errors.ToolError`，由上游 agent_core 捕获并转 `tool.error` 事件。

## 使用示例

```python
from tools import tool

@tool(name="add", description="把两个整数相加。")
def add(a: int, b: int) -> int:
    return a + b

assert get_tool("add").run({"a": 1, "b": 2}) == 3
```

详见各子模块 docstring 与 `tests/`。
