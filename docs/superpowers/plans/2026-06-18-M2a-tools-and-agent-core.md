# M2a：`packages/tools` + `packages/agent_core` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付两个生产级 SDK 包：`tools`（Tool 基类 + `@tool` 注册表 + 5 个内置工具）与 `agent_core`（state / events / runtime / checkpointer / interrupt + 4 个模式模板：ReAct / Plan-Execute / Reflection / Reflexion），覆盖率 ≥ 80%，达到 spec 第 9.M2 节"`packages/agent_core/patterns/react` 与第 4 章手写版本通过同一道测试题"的验收标准。

**Architecture:** 两个新包都是 uv workspace 成员、独立 src-layout、独立 pyproject.toml、独立 tests/。`tools` 单向依赖 `common`；`agent_core` 单向依赖 `common` + `llm_providers` + `tools`。所有 LLM 调用通过 LangChain `BaseChatModel` 抽象，单元测试用 `FakeListChatModel` / mock 替代真实调用。Tool 集成 LangChain `BaseTool` 让 LangGraph 的 `tool_calling_agent` 直接消费。State 用 `TypedDict` + `Annotated[T, reducer]`（spec §8.1 的官方推荐做法）。事件层设计成自定义 `AgentEvent` Pydantic 模型而非透传 LangGraph 原生事件（spec ADR-004）。

**Tech Stack:** Python 3.12, pydantic v2, langchain-core（`BaseTool` + `BaseChatModel`）, langgraph >= 0.2.50（`StateGraph` / `MemorySaver` / `interrupt`）, tenacity, structlog, pytest + pytest-asyncio + pytest-cov。Web 工具用 `httpx` + `tavily-python` + `trafilatura`（M2a 引入这些依赖）。

**Branch:** 从 `main` 创建新分支 `feat/m2a-tools-and-agent-core`。所有 commit 在该分支上，最终 fast-forward 合回 main。

**前置条件检查（执行者动手前确认）：**
1. 工作目录为 `/Users/temptrip/Documents/GitHub/AgentTask`，分支 `main`，HEAD 含 M1 全部成果（commit `c19a5be` 或更新）+ tag `m1-complete`。
2. M1 已交付：`packages/common`（config/logging/errors/retry/cost/cache）+ `packages/llm_providers`（factory/4 providers/middleware/embeddings）。本计划直接消费这些 API。
3. `make lint / type / test / coverage` 当前全绿（84 测试 + 覆盖率 ≥ 80%）。
4. 所有 commit 一律中文，Conventional Commits（`feat(<pkg>)` / `chore(<pkg>)` / `test(<pkg>)` / `docs(<pkg>)`）。
5. mypy.ini 已配 `namespace_packages = True` + `explicit_package_bases = True` + `mypy_path` 多包根。新包要扩展 `mypy_path` 一行。
6. `.pre-commit-config.yaml` 的 mypy hook `additional_dependencies` 已含 langchain-core/openai/anthropic/ollama/community 与 pydantic/structlog/tenacity/redis/fakeredis。新包再引入新库（如 langgraph、tavily、trafilatura）时要追加。
7. 每个新包都要给 `src/<pkg>/py.typed` 空文件（PEP 561 类型标记），否则 mypy 跨包引用会报 import-untyped。
8. workspace 子包内部装新依赖后，`uv sync --all-packages` 才会真正安装到 workspace venv（M1 已踩过坑）。

---

## File Structure 总览

```
packages/tools/
├── pyproject.toml                  # workspace 成员 + 运行时依赖
├── README.md                       # 包说明（中文）
├── src/tools/
│   ├── __init__.py                 # 公开 API: tool / get_tool / list_tools / Tool
│   ├── py.typed
│   ├── base.py                     # Tool 抽象基类（输入/输出 Pydantic）
│   ├── registry.py                 # @tool 装饰器 + 全局注册表
│   └── builtin/
│       ├── __init__.py             # re-export 5 个 builtin tool
│       ├── web_search.py           # Tavily web 搜索
│       ├── web_scrape.py           # trafilatura 抓取
│       ├── python_repl.py          # 受限 Python 求值（ast.literal_eval + 表达式白名单）
│       ├── file_io.py              # 路径白名单内的读/写
│       └── shell.py                # 命令白名单内的 subprocess
└── tests/
    ├── conftest.py                 # autouse env 隔离 + 注册表清理 fixture
    ├── test_base.py
    ├── test_registry.py
    └── builtin/
        ├── test_web_search.py
        ├── test_web_scrape.py
        ├── test_python_repl.py
        ├── test_file_io.py
        └── test_shell.py

packages/agent_core/
├── pyproject.toml                  # 依赖 common + llm_providers + tools + langgraph
├── README.md
├── src/agent_core/
│   ├── __init__.py                 # 公开 API: AgentEvent / build_<pattern>_graph / AgentRuntime / get_checkpointer / request_interrupt
│   ├── py.typed
│   ├── events.py                   # AgentEvent + 类型枚举
│   ├── state.py                    # BaseAgentState + 4 个 pattern 专用 state
│   ├── checkpointer.py             # get_checkpointer() 工厂（M2a 仅 MemorySaver；Postgres 留 M3 占位）
│   ├── interrupt.py                # request_interrupt() / resume_with() 包装
│   ├── runtime.py                  # AgentRuntime（invoke / astream + 错误兜底 + cost 集成）
│   └── patterns/
│       ├── __init__.py             # re-export 4 个 build_*_graph
│       ├── react.py                # build_react_graph
│       ├── plan_execute.py         # build_plan_execute_graph
│       ├── reflection.py           # build_reflection_graph
│       └── reflexion.py            # build_reflexion_graph + ExperienceStore protocol
└── tests/
    ├── conftest.py
    ├── test_events.py
    ├── test_state.py
    ├── test_checkpointer.py
    ├── test_interrupt.py
    ├── test_runtime.py
    └── patterns/
        ├── test_react.py
        ├── test_plan_execute.py
        ├── test_reflection.py
        └── test_reflexion.py

examples/m2a_react_demo.py           # 验收 demo（FakeListChatModel + 两个工具跑 ReAct）
tests/test_m2a_acceptance.py         # 跨包 smoke：每个 pattern 都用 fake LLM 跑通一道用例
```

---

## Task 1：创建 `packages/tools` 骨架

**Files:**
- Create: `packages/tools/pyproject.toml`
- Create: `packages/tools/README.md`
- Create: `packages/tools/src/tools/__init__.py`
- Create: `packages/tools/src/tools/py.typed`
- Create: `packages/tools/src/tools/builtin/__init__.py`
- Create: `packages/tools/tests/conftest.py`
- Modify: `pyproject.toml`（根 `dev` group 加 `respx` 已有，本 task 无需新增）
- Modify: `mypy.ini`（`mypy_path` 追加 `packages/tools/src`）

- [ ] **Step 1.1：切到新分支**

```bash
git switch -c feat/m2a-tools-and-agent-core main
```

Expected：`Switched to a new branch 'feat/m2a-tools-and-agent-core'`。

- [ ] **Step 1.2：创建目录与 pyproject**

```bash
mkdir -p packages/tools/src/tools/builtin packages/tools/tests/builtin
```

Create `packages/tools/pyproject.toml`：

```toml
[project]
name = "tools"
version = "0.1.0"
description = "AgentTask 工具层：Tool 基类 + @tool 注册表 + 内置工具（web / system）"
readme = "README.md"
requires-python = ">=3.12,<3.13"
license = { text = "MIT" }
authors = [{ name = "AgentTask Author" }]
dependencies = [
    "common",
    "pydantic>=2.9,<3",
    "langchain-core>=0.3.20,<0.4",
    "httpx>=0.27,<0.29",
    "tavily-python>=0.5,<1",
    "trafilatura>=1.12,<2",
    "readability-lxml>=0.8,<1",
]

[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/tools"]

[tool.hatch.build.targets.sdist]
include = ["src/tools", "README.md"]

[tool.uv.sources]
common = { workspace = true }
```

- [ ] **Step 1.3：创建 README**

Create `packages/tools/README.md`：

````markdown
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
````

- [ ] **Step 1.4：创建 `__init__.py` 占位**

Create `packages/tools/src/tools/__init__.py`：

```python
"""tools: AgentTask 工具层。

公开 API（M2a 期间逐 task 填充）:
- Tool: 基类
- tool: 装饰器
- get_tool / list_tools: 注册表查询
"""

from __future__ import annotations

__version__ = "0.1.0"
```

Create `packages/tools/src/tools/py.typed`（空文件）。

Create `packages/tools/src/tools/builtin/__init__.py`：

```python
"""内置工具集合。具体工具在后续 task 中加入。"""

from __future__ import annotations
```

- [ ] **Step 1.5：写共用 conftest.py**

Create `packages/tools/tests/conftest.py`：

```python
"""packages/tools 测试共用 fixtures。"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """每个测试前清空 AGENTTASK_ 与 TAVILY_ 前缀环境变量。"""
    for key in list(os.environ.keys()):
        if key.startswith(("AGENTTASK_", "TAVILY_")):
            monkeypatch.delenv(key, raising=False)
    yield


@pytest.fixture(autouse=True)
def _clear_registry() -> Iterator[None]:
    """每个测试前后清空 tools 全局注册表,避免互相污染。

    `tools.registry` 在 Task 3 引入,先尝试 import,失败则跳过(Task 1/2 测试不依赖)。
    """
    try:
        from tools import registry as _registry
    except ImportError:
        yield
        return
    _registry._REGISTRY.clear()
    yield
    _registry._REGISTRY.clear()
```

- [ ] **Step 1.6：扩展 mypy.ini 多包根**

Modify `mypy.ini`，把 `mypy_path` 那一行改为：

```ini
mypy_path = packages/common/src:packages/llm_providers/src:packages/tools/src:packages/agent_core/src
```

（`packages/agent_core/src` 在 Task 6 才会存在,先填上不影响——mypy 找不到的目录会安静跳过。）

- [ ] **Step 1.7：扩展 pre-commit mypy 依赖**

Modify `.pre-commit-config.yaml`，在 mypy hook 的 `additional_dependencies` 末尾追加：

```yaml
          - httpx>=0.27
          - tavily-python>=0.5
          - trafilatura>=1.12
          - langgraph>=0.2.50
```

- [ ] **Step 1.8：同步依赖**

```bash
uv sync --all-packages
```

Expected：解析并安装 `tavily-python` / `trafilatura` / `readability-lxml`。`packages/tools` 作为 workspace 成员被识别。

- [ ] **Step 1.9：跑 lint + type 验证骨架**

```bash
uv run ruff check packages/tools
uv run mypy packages/tools
```

Expected：均通过。

- [ ] **Step 1.10：提交**

```bash
git add packages/tools/pyproject.toml packages/tools/README.md packages/tools/src packages/tools/tests/conftest.py mypy.ini .pre-commit-config.yaml uv.lock
git commit -m "feat(tools): 创建 packages/tools 包骨架（src-layout + 运行时依赖）"
```

---

## Task 2：`tools.base` —— Tool 抽象基类（TDD）

**Files:**
- Create: `packages/tools/tests/test_base.py`
- Create: `packages/tools/src/tools/base.py`

**设计要点：**
- `Tool` 继承 `langchain_core.tools.BaseTool`，让 LangGraph `tool_calling_agent` / `bind_tools` 直接消费。
- 用户子类化 `Tool` 时定义 `args_schema: type[BaseModel]`（输入）+ `output_schema: type[BaseModel] | None`（输出，可选）。
- 实际执行逻辑放 `_run(self, **kwargs) -> Any`（同步）/ `_arun(self, **kwargs) -> Any`（async），错误被包装为 `ToolError`。
- 元数据字段：`require_approval: bool`（M4 HITL 用）/ `timeout_s: float | None`（M4 sandbox 用）。

- [ ] **Step 2.1：写失败的测试**

Create `packages/tools/tests/test_base.py`：

```python
"""Tool 基类行为测试。"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from common.errors import ToolError
from tools.base import Tool


class _AddInput(BaseModel):
    a: int
    b: int


class _Add(Tool):
    name: str = "add"
    description: str = "把两个整数相加。"
    args_schema: type[BaseModel] = _AddInput

    def _run(self, a: int, b: int) -> int:  # type: ignore[override]
        return a + b


class _Boom(Tool):
    name: str = "boom"
    description: str = "故意失败。"
    args_schema: type[BaseModel] = _AddInput

    def _run(self, a: int, b: int) -> int:  # type: ignore[override]
        raise RuntimeError("kaboom")


@pytest.mark.fast
def test_tool_run_returns_value() -> None:
    """子类 _run 返回值应直接传出。"""
    assert _Add().run({"a": 1, "b": 2}) == 3


@pytest.mark.fast
def test_tool_validates_input() -> None:
    """缺字段应抛 pydantic ValidationError → 我们包装为 ToolError。"""
    with pytest.raises(ToolError, match="add"):
        _Add().run({"a": 1})  # 缺 b


@pytest.mark.fast
def test_tool_wraps_runtime_error_as_toolerror() -> None:
    """_run 抛任何异常都应被包装为 ToolError(tool_name=...)。"""
    with pytest.raises(ToolError) as exc_info:
        _Boom().run({"a": 1, "b": 2})
    assert exc_info.value.tool_name == "boom"
    assert "kaboom" in str(exc_info.value)


@pytest.mark.fast
def test_tool_default_metadata() -> None:
    """require_approval 默认 False,timeout_s 默认 None。"""
    t = _Add()
    assert t.require_approval is False
    assert t.timeout_s is None


@pytest.mark.fast
def test_tool_inherits_basetool() -> None:
    """Tool 必须继承 langchain_core BaseTool,以便 LangGraph 消费。"""
    from langchain_core.tools import BaseTool

    assert issubclass(Tool, BaseTool)


@pytest.mark.fast
async def test_tool_arun_default_falls_back_to_sync() -> None:
    """未 override _arun 时,arun 默认走同步实现。"""
    result = await _Add().arun({"a": 5, "b": 7})
    assert result == 12
```

- [ ] **Step 2.2：跑测试确认失败**

```bash
uv run pytest packages/tools/tests/test_base.py -v
```

Expected：ImportError(`tools.base` 不存在)。

- [ ] **Step 2.3：实现 base 模块**

Create `packages/tools/src/tools/base.py`：

```python
"""Tool 抽象基类。

继承 langchain_core BaseTool 让 LangGraph 直接消费;同时统一错误处理与
仓库特有元数据(require_approval / timeout_s)。
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool
from pydantic import ValidationError

from common.errors import ToolError


class Tool(BaseTool):
    """所有仓库工具的统一基类。

    子类必须定义:
    - name: str
    - description: str
    - args_schema: type[BaseModel]
    - _run(self, **kwargs) -> Any  (同步实现)

    可选 override:
    - _arun(self, **kwargs) -> Any  (async 实现,不 override 时 LangChain 会调同步版本)

    仓库特有元数据(LangChain BaseTool 没有,此处扩展):
    - require_approval: bool —— M4 HITL 高危工具审批门;M2a 默认 False。
    - timeout_s: float | None —— M4 sandbox 超时;M2a 默认 None。
    """

    require_approval: bool = False
    timeout_s: float | None = None

    def run(  # type: ignore[override]
        self,
        tool_input: str | dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """同步执行入口。捕获所有异常 → 包装为 ToolError。"""
        try:
            return super().run(tool_input, *args, **kwargs)
        except ValidationError as e:
            raise ToolError(
                f"input validation failed for tool {self.name!r}: {e}",
                tool_name=self.name,
                context={"errors": e.errors()},
            ) from e
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(
                f"tool {self.name!r} raised {type(e).__name__}: {e}",
                tool_name=self.name,
            ) from e

    async def arun(  # type: ignore[override]
        self,
        tool_input: str | dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """异步执行入口。捕获所有异常 → 包装为 ToolError。"""
        try:
            return await super().arun(tool_input, *args, **kwargs)
        except ValidationError as e:
            raise ToolError(
                f"input validation failed for tool {self.name!r}: {e}",
                tool_name=self.name,
                context={"errors": e.errors()},
            ) from e
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(
                f"tool {self.name!r} raised {type(e).__name__}: {e}",
                tool_name=self.name,
            ) from e


__all__ = ["Tool"]
```

- [ ] **Step 2.4：跑测试确认通过**

```bash
uv run pytest packages/tools/tests/test_base.py -v
```

Expected：6 个测试全过。

- [ ] **Step 2.5：lint + type**

```bash
uv run ruff check packages/tools
uv run mypy packages/tools
```

Expected：均通过。

- [ ] **Step 2.6：提交**

```bash
git add packages/tools/src/tools/base.py packages/tools/tests/test_base.py
git commit -m "feat(tools): 添加 Tool 基类（继承 BaseTool + 统一 ToolError 包装）"
```

---

## Task 3：`tools.registry` —— `@tool` 装饰器与全局注册表（TDD）

**Files:**
- Create: `packages/tools/tests/test_registry.py`
- Create: `packages/tools/src/tools/registry.py`
- Modify: `packages/tools/src/tools/__init__.py`（re-export）

**设计要点：**
- 全局 `_REGISTRY: dict[str, Tool]`。
- `@tool(name, description, ...)` 把普通函数（含 type hints）转成 `Tool` 子类实例并注册。
- 函数签名 → 自动生成 `args_schema`（用 `pydantic.create_model`）。
- `get_tool(name)` / `list_tools()` 查询。
- 重复注册抛 `ConfigError`。

- [ ] **Step 3.1：写失败的测试**

Create `packages/tools/tests/test_registry.py`：

```python
"""@tool 装饰器与注册表测试。"""

from __future__ import annotations

import pytest

from common.errors import ConfigError
from tools import Tool, get_tool, list_tools, tool


@pytest.mark.fast
def test_tool_decorator_registers_function() -> None:
    """@tool 应创建 Tool 实例并注册。"""

    @tool(name="echo", description="原样返回字符串。")
    def echo(text: str) -> str:
        return text

    t = get_tool("echo")
    assert isinstance(t, Tool)
    assert t.name == "echo"
    assert t.description == "原样返回字符串。"
    assert t.run({"text": "hi"}) == "hi"


@pytest.mark.fast
def test_tool_decorator_infers_schema() -> None:
    """从函数签名自动推 args_schema。"""

    @tool(name="add", description="加法。")
    def add(a: int, b: int = 10) -> int:
        return a + b

    t = get_tool("add")
    assert t.run({"a": 5}) == 15  # 用默认值
    assert t.run({"a": 5, "b": 3}) == 8


@pytest.mark.fast
def test_list_tools_returns_all() -> None:
    """list_tools 返回所有已注册工具。"""

    @tool(name="t1", description="x")
    def t1() -> str:
        return "1"

    @tool(name="t2", description="y")
    def t2() -> str:
        return "2"

    names = {t.name for t in list_tools()}
    assert {"t1", "t2"} <= names


@pytest.mark.fast
def test_duplicate_name_raises() -> None:
    """重复注册同名工具应抛 ConfigError。"""

    @tool(name="dup", description="first")
    def first() -> str:
        return "1"

    with pytest.raises(ConfigError, match="dup"):

        @tool(name="dup", description="second")
        def second() -> str:
            return "2"


@pytest.mark.fast
def test_get_tool_unknown_raises() -> None:
    """未注册名查询应抛 ConfigError。"""
    with pytest.raises(ConfigError, match="not-registered"):
        get_tool("not-registered")


@pytest.mark.fast
async def test_tool_decorator_async_function() -> None:
    """async 函数应同样可被注册,arun 时正确执行。"""

    @tool(name="aecho", description="async echo")
    async def aecho(text: str) -> str:
        return text.upper()

    t = get_tool("aecho")
    result = await t.arun({"text": "hi"})
    assert result == "HI"


@pytest.mark.fast
def test_tool_decorator_passes_metadata() -> None:
    """require_approval / timeout_s 应传到 Tool 实例。"""

    @tool(name="risky", description="x", require_approval=True, timeout_s=5.0)
    def risky() -> str:
        return "ok"

    t = get_tool("risky")
    assert t.require_approval is True
    assert t.timeout_s == 5.0
```

- [ ] **Step 3.2：跑测试确认失败**

```bash
uv run pytest packages/tools/tests/test_registry.py -v
```

Expected：ImportError。

- [ ] **Step 3.3：实现 registry**

Create `packages/tools/src/tools/registry.py`：

```python
"""@tool 装饰器与全局注册表。

设计:
- 装饰器读函数签名,用 pydantic.create_model 生成 args_schema。
- 同步函数 → _run;async 函数 → _arun(同步 _run 走 LangChain 默认 fallback)。
- 注册表是模块级 dict;测试 fixture 在每个测试前后清空。
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, create_model

from common.errors import ConfigError

from .base import Tool

_REGISTRY: dict[str, Tool] = {}


def _build_args_schema(func: Callable[..., Any], schema_name: str) -> type[BaseModel]:
    """从函数签名生成 pydantic args_schema。

    跳过 self / cls / *args / **kwargs。无 default 的字段标 required。
    """
    sig = inspect.signature(func)
    fields: dict[str, Any] = {}
    for pname, param in sig.parameters.items():
        if pname in {"self", "cls"}:
            continue
        if param.kind in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}:
            continue
        annotation = param.annotation if param.annotation is not inspect.Parameter.empty else Any
        default = param.default if param.default is not inspect.Parameter.empty else ...
        fields[pname] = (annotation, default)
    return create_model(schema_name, **fields)  # type: ignore[call-overload, no-any-return]


def tool(
    *,
    name: str,
    description: str,
    require_approval: bool = False,
    timeout_s: float | None = None,
) -> Callable[[Callable[..., Any]], Tool]:
    """把函数注册为工具,返回 Tool 实例(替代原函数)。

    Args:
        name: 工具名(全局唯一)。
        description: 描述,会传给 LLM 做 tool selection。
        require_approval: 高危工具,M4 HITL 会拦截。
        timeout_s: 超时秒数,M4 sandbox 用。

    Raises:
        ConfigError: 重名注册。
    """

    def decorator(func: Callable[..., Any]) -> Tool:
        if name in _REGISTRY:
            raise ConfigError(
                f"tool name {name!r} already registered (existing: {_REGISTRY[name]!r})",
                context={"name": name},
            )

        schema_cls = _build_args_schema(func, schema_name=f"{name}__Args")
        is_async = asyncio.iscoroutinefunction(func)

        class _DecoratedTool(Tool):
            # 显式声明类型,避免 mypy 把基类字段视为 ClassVar
            name: str = name  # type: ignore[assignment]
            description: str = description  # type: ignore[assignment]
            args_schema: type[BaseModel] = schema_cls  # type: ignore[assignment]
            require_approval: bool = require_approval
            timeout_s: float | None = timeout_s

            def _run(self, **kwargs: Any) -> Any:
                if is_async:
                    coro: Awaitable[Any] = func(**kwargs)
                    return asyncio.run(coro)
                return func(**kwargs)

            async def _arun(self, **kwargs: Any) -> Any:
                if is_async:
                    return await func(**kwargs)
                return func(**kwargs)

        instance = _DecoratedTool()
        _REGISTRY[name] = instance
        return instance

    return decorator


def get_tool(name: str) -> Tool:
    """按名查工具。未注册抛 ConfigError。"""
    if name not in _REGISTRY:
        raise ConfigError(
            f"tool not registered: {name!r}; known: {sorted(_REGISTRY)}",
            context={"name": name},
        )
    return _REGISTRY[name]


def list_tools() -> list[Tool]:
    """返回所有已注册工具(顺序 = 注册顺序)。"""
    return list(_REGISTRY.values())


__all__ = ["get_tool", "list_tools", "tool"]
```

- [ ] **Step 3.4：在 `__init__.py` re-export**

Replace `packages/tools/src/tools/__init__.py`：

```python
"""tools: AgentTask 工具层。

公开 API:
- Tool: 抽象基类
- tool: 装饰器(自动注册)
- get_tool / list_tools: 注册表查询
"""

from __future__ import annotations

from .base import Tool
from .registry import get_tool, list_tools, tool

__version__ = "0.1.0"

__all__ = ["__version__", "Tool", "get_tool", "list_tools", "tool"]
```

- [ ] **Step 3.5：跑测试确认通过**

```bash
uv run pytest packages/tools/tests/test_registry.py -v
```

Expected：7 个测试全过。

- [ ] **Step 3.6：lint + type**

```bash
uv run ruff check packages/tools
uv run mypy packages/tools
```

Expected：均通过。

- [ ] **Step 3.7：提交**

```bash
git add packages/tools/src/tools/registry.py packages/tools/src/tools/__init__.py packages/tools/tests/test_registry.py
git commit -m "feat(tools): 添加 @tool 装饰器与全局注册表"
```

---

## Task 4：`tools.builtin` web 工具组（TDD）—— `web_search` + `web_scrape`

**Files:**
- Create: `packages/tools/tests/builtin/test_web_search.py`
- Create: `packages/tools/tests/builtin/test_web_scrape.py`
- Create: `packages/tools/src/tools/builtin/web_search.py`
- Create: `packages/tools/src/tools/builtin/web_scrape.py`
- Modify: `packages/tools/src/tools/builtin/__init__.py`

**设计要点：**
- `web_search`：Tavily 客户端;key 从 `Settings.tavily_api_key` 读。返回 `list[dict]` 标准化结果。
- `web_scrape`：`httpx` 拉 HTML → `trafilatura.extract` 提正文。fallback 到 `readability-lxml`。
- 单元测试用 `respx` mock httpx,不发真实 HTTP。

- [ ] **Step 4.1：写 web_search 测试**

Create `packages/tools/tests/builtin/__init__.py`（空文件）。

Create `packages/tools/tests/builtin/test_web_search.py`：

```python
"""web_search 工具测试(用 mock,不发真请求)。"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from common.errors import ConfigError, ToolError
from tools.builtin.web_search import web_search


@pytest.mark.fast
def test_web_search_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """无 TAVILY_API_KEY 应抛 ConfigError。"""
    with pytest.raises((ConfigError, ToolError), match="TAVILY"):
        web_search.run({"query": "hello"})


@pytest.mark.fast
def test_web_search_returns_normalized_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """成功返回 list[dict]:title / url / content / score。"""
    monkeypatch.setenv("AGENTTASK_TAVILY_API_KEY", "tvly-test")  # pragma: allowlist secret

    fake_client = MagicMock()
    fake_client.search.return_value = {
        "results": [
            {
                "title": "Doc A",
                "url": "https://a.com",
                "content": "snippet a",
                "score": 0.9,
            },
            {
                "title": "Doc B",
                "url": "https://b.com",
                "content": "snippet b",
                "score": 0.7,
            },
        ]
    }

    def fake_factory(*_: Any, **__: Any) -> MagicMock:
        return fake_client

    monkeypatch.setattr("tools.builtin.web_search._get_client", fake_factory)

    out = web_search.run({"query": "anything", "max_results": 2})
    assert isinstance(out, list)
    assert len(out) == 2
    assert out[0]["title"] == "Doc A"
    assert out[0]["url"] == "https://a.com"
    assert out[0]["score"] == 0.9


@pytest.mark.fast
def test_web_search_max_results_passed_to_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """max_results 应透传给 tavily client.search。"""
    monkeypatch.setenv("AGENTTASK_TAVILY_API_KEY", "tvly-test")  # pragma: allowlist secret

    fake_client = MagicMock()
    fake_client.search.return_value = {"results": []}
    monkeypatch.setattr(
        "tools.builtin.web_search._get_client", lambda: fake_client
    )

    web_search.run({"query": "x", "max_results": 7})
    args, kwargs = fake_client.search.call_args
    # tavily-python 的 search 签名: search(query, max_results=...)
    assert kwargs.get("max_results") == 7 or (len(args) >= 2 and args[1] == 7)
```

- [ ] **Step 4.2：写 web_scrape 测试**

Create `packages/tools/tests/builtin/test_web_scrape.py`：

```python
"""web_scrape 工具测试(用 respx mock httpx)。"""

from __future__ import annotations

import httpx
import pytest
import respx

from common.errors import ToolError
from tools.builtin.web_scrape import web_scrape

_HTML_PAGE = """
<html>
  <head><title>测试页</title></head>
  <body>
    <article>
      <h1>主标题</h1>
      <p>这是一段比较长的正文,长度足够 trafilatura 提取出来。</p>
      <p>第二段正文,带 <a href="/x">内部链接</a>。</p>
    </article>
    <nav>跳过的导航</nav>
  </body>
</html>
""".strip()


@pytest.mark.fast
@respx.mock
def test_web_scrape_extracts_main_content() -> None:
    """trafilatura 应提取 <article> 内的正文,跳过导航。"""
    respx.get("https://example.com/x").mock(
        return_value=httpx.Response(200, text=_HTML_PAGE)
    )
    out = web_scrape.run({"url": "https://example.com/x"})
    assert isinstance(out, dict)
    assert "主标题" in out["content"] or "正文" in out["content"]
    assert out["url"] == "https://example.com/x"


@pytest.mark.fast
@respx.mock
def test_web_scrape_404_raises_toolerror() -> None:
    """非 2xx 状态应抛 ToolError(tool_name=web_scrape)。"""
    respx.get("https://example.com/missing").mock(
        return_value=httpx.Response(404, text="not found")
    )
    with pytest.raises(ToolError) as exc_info:
        web_scrape.run({"url": "https://example.com/missing"})
    assert exc_info.value.tool_name == "web_scrape"
    assert "404" in str(exc_info.value)


@pytest.mark.fast
@respx.mock
def test_web_scrape_timeout_raises_toolerror() -> None:
    """httpx 超时应包装为 ToolError。"""
    respx.get("https://slow.example.com").mock(side_effect=httpx.TimeoutException)
    with pytest.raises(ToolError, match="web_scrape"):
        web_scrape.run({"url": "https://slow.example.com"})
```

- [ ] **Step 4.3：跑测试确认失败**

```bash
uv run pytest packages/tools/tests/builtin -v
```

Expected：ImportError。

- [ ] **Step 4.4：实现 web_search**

Create `packages/tools/src/tools/builtin/web_search.py`：

```python
"""Tavily 网页搜索工具。"""

from __future__ import annotations

from typing import Any

from common.config import get_settings
from common.errors import ConfigError
from tools.registry import tool


def _get_client() -> Any:
    """构造 tavily client(单独函数以便测试 mock)。"""
    from tavily import TavilyClient

    settings = get_settings(reload=True)
    if settings.tavily_api_key is None:
        raise ConfigError(
            "missing AGENTTASK_TAVILY_API_KEY",
            context={"tool": "web_search"},
        )
    return TavilyClient(api_key=settings.tavily_api_key.get_secret_value())


@tool(
    name="web_search",
    description="用 Tavily 搜索网络,返回排序后的相关网页列表(title/url/content/score)。",
)
def web_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """搜索网络。

    Args:
        query: 搜索关键词或自然语言问题。
        max_results: 返回结果数,1-10。

    Returns:
        list[dict]: 每项含 title / url / content / score。
    """
    client = _get_client()
    raw = client.search(query, max_results=max_results)
    results: list[dict[str, Any]] = raw.get("results", [])
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": float(r.get("score", 0.0)),
        }
        for r in results
    ]


__all__ = ["web_search"]
```

- [ ] **Step 4.5：实现 web_scrape**

Create `packages/tools/src/tools/builtin/web_scrape.py`：

```python
"""trafilatura 网页正文抓取工具。"""

from __future__ import annotations

from typing import Any

import httpx
import trafilatura

from common.errors import ToolError
from tools.registry import tool

_TIMEOUT_S = 15.0
_USER_AGENT = "AgentTask/0.1 (+https://github.com/zhanglkx/AgentTask)"


@tool(
    name="web_scrape",
    description="抓取指定 URL 的主体正文(自动跳过导航/广告/侧栏)。",
)
def web_scrape(url: str) -> dict[str, Any]:
    """抓取并提取正文。

    Args:
        url: 目标网页 URL(http/https)。

    Returns:
        dict: {"url": str, "content": str, "title": str | None}
    """
    try:
        with httpx.Client(
            timeout=_TIMEOUT_S, headers={"User-Agent": _USER_AGENT}
        ) as client:
            resp = client.get(url, follow_redirects=True)
    except httpx.HTTPError as e:
        raise ToolError(
            f"web_scrape http error for {url}: {type(e).__name__}: {e}",
            tool_name="web_scrape",
            context={"url": url},
        ) from e

    if resp.status_code >= 400:
        raise ToolError(
            f"web_scrape got HTTP {resp.status_code} for {url}",
            tool_name="web_scrape",
            context={"url": url, "status": resp.status_code},
        )

    extracted = trafilatura.extract(
        resp.text,
        include_comments=False,
        include_tables=True,
        favor_recall=True,
    )
    if not extracted:
        # fallback: 用 readability-lxml
        try:
            from readability import Document  # type: ignore[import-untyped]

            doc = Document(resp.text)
            extracted = doc.summary()
        except Exception:  # noqa: BLE001
            extracted = ""

    title: str | None = None
    try:
        meta = trafilatura.extract_metadata(resp.text)
        if meta is not None:
            title = meta.title
    except Exception:  # noqa: BLE001
        pass

    return {"url": url, "content": extracted or "", "title": title}


__all__ = ["web_scrape"]
```

- [ ] **Step 4.6：在 builtin `__init__.py` re-export**

Replace `packages/tools/src/tools/builtin/__init__.py`：

```python
"""内置工具集合。"""

from __future__ import annotations

from .web_scrape import web_scrape
from .web_search import web_search

__all__ = ["web_scrape", "web_search"]
```

- [ ] **Step 4.7：跑测试确认通过**

```bash
uv run pytest packages/tools/tests/builtin -v
```

Expected：6 个测试全过(3 + 3)。

- [ ] **Step 4.8：lint + type**

```bash
uv run ruff check packages/tools
uv run mypy packages/tools
```

Expected：均通过。

- [ ] **Step 4.9：提交**

```bash
git add packages/tools/src/tools/builtin/web_search.py packages/tools/src/tools/builtin/web_scrape.py packages/tools/src/tools/builtin/__init__.py packages/tools/tests/builtin/__init__.py packages/tools/tests/builtin/test_web_search.py packages/tools/tests/builtin/test_web_scrape.py
git commit -m "feat(tools): 添加 web 工具组（web_search Tavily + web_scrape trafilatura）"
```

---

## Task 5：`tools.builtin` 系统工具组（TDD）—— `python_repl` + `file_io` + `shell`

**Files:**
- Create: `packages/tools/tests/builtin/test_python_repl.py`
- Create: `packages/tools/tests/builtin/test_file_io.py`
- Create: `packages/tools/tests/builtin/test_shell.py`
- Create: `packages/tools/src/tools/builtin/python_repl.py`
- Create: `packages/tools/src/tools/builtin/file_io.py`
- Create: `packages/tools/src/tools/builtin/shell.py`
- Modify: `packages/tools/src/tools/builtin/__init__.py`

**设计要点：**
- `python_repl`：M2a 的版本是**安全简版**(`ast.literal_eval` + 简单算术),不跑任意代码;真实 sandbox 留给 M4 `packages/sandbox`。`require_approval=True` 显式标记。
- `file_io`：必须传 `allowed_root` 参数(每次调用),路径越界抛 `ToolError`。两种 action: `read` / `write`。
- `shell`：每次调用必须带白名单 `allowed_commands: list[str]`(命令名,不是完整命令行),超出抛错。`require_approval=True`。

- [ ] **Step 5.1：写 python_repl 测试**

Create `packages/tools/tests/builtin/test_python_repl.py`：

```python
"""python_repl 工具测试(M2a 安全简版)。"""

from __future__ import annotations

import pytest

from common.errors import ToolError
from tools.builtin.python_repl import python_repl


@pytest.mark.fast
def test_python_repl_arithmetic() -> None:
    """支持基本算术表达式。"""
    assert python_repl.run({"expression": "1 + 2 * 3"}) == 7
    assert python_repl.run({"expression": "(10 - 4) / 2"}) == 3.0


@pytest.mark.fast
def test_python_repl_literals() -> None:
    """支持 list / dict / str / 数字字面量。"""
    assert python_repl.run({"expression": "[1, 2, 3]"}) == [1, 2, 3]
    assert python_repl.run({"expression": "{'a': 1}"}) == {"a": 1}
    assert python_repl.run({"expression": "'hello'"}) == "hello"


@pytest.mark.fast
def test_python_repl_blocks_function_call() -> None:
    """禁止函数调用(避免任意代码执行)。"""
    with pytest.raises(ToolError, match="not allowed"):
        python_repl.run({"expression": "__import__('os').system('rm -rf /')"})


@pytest.mark.fast
def test_python_repl_blocks_attribute_access() -> None:
    """禁止属性访问(防止 ()._dunder 越权)。"""
    with pytest.raises(ToolError, match="not allowed"):
        python_repl.run({"expression": "(1).__class__"})


@pytest.mark.fast
def test_python_repl_marks_require_approval() -> None:
    """python_repl 默认应标 require_approval=True。"""
    assert python_repl.require_approval is True


@pytest.mark.fast
def test_python_repl_syntax_error_raises_toolerror() -> None:
    """语法错误应抛 ToolError。"""
    with pytest.raises(ToolError, match="python_repl"):
        python_repl.run({"expression": "1 +"})
```

- [ ] **Step 5.2：写 file_io 测试**

Create `packages/tools/tests/builtin/test_file_io.py`：

```python
"""file_io 工具测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from common.errors import ToolError
from tools.builtin.file_io import file_io


@pytest.mark.fast
def test_file_io_read_within_root(tmp_path: Path) -> None:
    """读取 allowed_root 下的文件应成功。"""
    f = tmp_path / "hello.txt"
    f.write_text("世界", encoding="utf-8")

    out = file_io.run(
        {
            "action": "read",
            "path": str(f),
            "allowed_root": str(tmp_path),
        }
    )
    assert out == "世界"


@pytest.mark.fast
def test_file_io_write_within_root(tmp_path: Path) -> None:
    """写入 allowed_root 下的文件应成功。"""
    f = tmp_path / "out.txt"
    file_io.run(
        {
            "action": "write",
            "path": str(f),
            "allowed_root": str(tmp_path),
            "content": "hi",
        }
    )
    assert f.read_text(encoding="utf-8") == "hi"


@pytest.mark.fast
def test_file_io_path_escape_raises(tmp_path: Path) -> None:
    """越出 allowed_root 应抛 ToolError。"""
    outside = tmp_path.parent / "secret.txt"
    with pytest.raises(ToolError, match="outside allowed_root"):
        file_io.run(
            {
                "action": "read",
                "path": str(outside),
                "allowed_root": str(tmp_path),
            }
        )


@pytest.mark.fast
def test_file_io_unknown_action_raises(tmp_path: Path) -> None:
    """非 read/write 的 action 应抛 ToolError。"""
    with pytest.raises(ToolError, match="action"):
        file_io.run(
            {
                "action": "delete",  # 未支持
                "path": str(tmp_path / "x"),
                "allowed_root": str(tmp_path),
            }
        )


@pytest.mark.fast
def test_file_io_read_missing_file_raises(tmp_path: Path) -> None:
    """读不存在文件应抛 ToolError。"""
    with pytest.raises(ToolError, match="file_io"):
        file_io.run(
            {
                "action": "read",
                "path": str(tmp_path / "nope.txt"),
                "allowed_root": str(tmp_path),
            }
        )
```

- [ ] **Step 5.3：写 shell 测试**

Create `packages/tools/tests/builtin/test_shell.py`：

```python
"""shell 工具测试。"""

from __future__ import annotations

import pytest

from common.errors import ToolError
from tools.builtin.shell import shell


@pytest.mark.fast
def test_shell_runs_whitelisted_command() -> None:
    """白名单内的命令应正常执行并返回 stdout。"""
    out = shell.run(
        {
            "argv": ["echo", "hello"],
            "allowed_commands": ["echo"],
        }
    )
    assert out["returncode"] == 0
    assert "hello" in out["stdout"]


@pytest.mark.fast
def test_shell_rejects_non_whitelisted_command() -> None:
    """白名单外的命令应抛 ToolError。"""
    with pytest.raises(ToolError, match="not in allowed_commands"):
        shell.run(
            {
                "argv": ["rm", "-rf", "/"],
                "allowed_commands": ["echo", "ls"],
            }
        )


@pytest.mark.fast
def test_shell_returns_nonzero_on_failure() -> None:
    """失败的命令(returncode != 0)不抛错,但在结果里体现。"""
    out = shell.run(
        {
            "argv": ["false"],
            "allowed_commands": ["false"],
        }
    )
    assert out["returncode"] != 0


@pytest.mark.fast
def test_shell_marks_require_approval() -> None:
    """shell 默认应标 require_approval=True。"""
    assert shell.require_approval is True


@pytest.mark.fast
def test_shell_empty_argv_raises() -> None:
    """空 argv 应抛 ToolError。"""
    with pytest.raises(ToolError, match="argv"):
        shell.run({"argv": [], "allowed_commands": ["echo"]})
```

- [ ] **Step 5.4：跑测试确认失败**

```bash
uv run pytest packages/tools/tests/builtin -v
```

Expected：3 个新测试文件 ImportError。

- [ ] **Step 5.5：实现 python_repl(安全简版)**

Create `packages/tools/src/tools/builtin/python_repl.py`：

```python
"""安全简版 Python 表达式求值工具。

M2a 阶段:仅支持算术 + 字面量,通过 AST 白名单实现。
真实代码沙箱(任意函数调用 / import 等)留给 M4 `packages/sandbox`。
"""

from __future__ import annotations

import ast
import operator as op
from typing import Any

from common.errors import ToolError
from tools.registry import tool

_BIN_OPS: dict[type[ast.operator], Any] = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
}

_UNARY_OPS: dict[type[ast.unaryop], Any] = {
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}

_ALLOWED_NODES: tuple[type[ast.AST], ...] = (
    ast.Expression,
    ast.Constant,
    ast.BinOp,
    ast.UnaryOp,
    ast.List,
    ast.Tuple,
    ast.Dict,
    ast.Set,
)


def _eval_node(node: ast.AST) -> Any:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        op_func = _BIN_OPS.get(type(node.op))
        if op_func is None:
            raise ToolError(
                f"binary op {type(node.op).__name__} not allowed",
                tool_name="python_repl",
            )
        return op_func(_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        op_func = _UNARY_OPS.get(type(node.op))
        if op_func is None:
            raise ToolError(
                f"unary op {type(node.op).__name__} not allowed",
                tool_name="python_repl",
            )
        return op_func(_eval_node(node.operand))
    if isinstance(node, ast.List):
        return [_eval_node(e) for e in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(e) for e in node.elts)
    if isinstance(node, ast.Dict):
        return {
            _eval_node(k) if k else None: _eval_node(v)
            for k, v in zip(node.keys, node.values, strict=True)
        }
    if isinstance(node, ast.Set):
        return {_eval_node(e) for e in node.elts}
    raise ToolError(
        f"AST node {type(node).__name__} not allowed in python_repl",
        tool_name="python_repl",
    )


@tool(
    name="python_repl",
    description="求值受限 Python 表达式(仅算术 + list/dict/tuple/set 字面量,无函数调用)。",
    require_approval=True,
)
def python_repl(expression: str) -> Any:
    """求值表达式。

    Args:
        expression: 单行表达式(no statements)。

    Returns:
        Any: 求值结果。
    """
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise ToolError(
            f"python_repl syntax error: {e}",
            tool_name="python_repl",
        ) from e

    # 先扫一遍所有节点,确保都在白名单内
    for sub in ast.walk(tree):
        if not isinstance(sub, (*_ALLOWED_NODES, ast.operator, ast.unaryop)):
            raise ToolError(
                f"AST node {type(sub).__name__} not allowed in python_repl",
                tool_name="python_repl",
            )
    return _eval_node(tree)


__all__ = ["python_repl"]
```

- [ ] **Step 5.6：实现 file_io**

Create `packages/tools/src/tools/builtin/file_io.py`：

```python
"""路径白名单内的文件读/写工具。"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from common.errors import ToolError
from tools.registry import tool


def _resolve_within(allowed_root: str, path: str) -> Path:
    """把 path 解析为绝对路径,并校验落在 allowed_root 之内。"""
    root = Path(allowed_root).resolve()
    target = Path(path).resolve()
    try:
        target.relative_to(root)
    except ValueError as e:
        raise ToolError(
            f"path {target} is outside allowed_root {root}",
            tool_name="file_io",
            context={"path": str(target), "allowed_root": str(root)},
        ) from e
    return target


@tool(
    name="file_io",
    description="读/写文件。必须提供 allowed_root,所有操作严格限定在该目录下。",
)
def file_io(
    action: Literal["read", "write"],
    path: str,
    allowed_root: str,
    content: str = "",
) -> str:
    """文件读写。

    Args:
        action: read 或 write。
        path: 目标文件路径(绝对或相对均可,会与 allowed_root 解析比较)。
        allowed_root: 允许操作的根目录(必填)。
        content: 仅在 write 时使用。

    Returns:
        str: read 返回文件内容;write 返回 "ok"。
    """
    if action not in ("read", "write"):
        raise ToolError(
            f"file_io action must be 'read' or 'write', got {action!r}",
            tool_name="file_io",
        )

    target = _resolve_within(allowed_root, path)

    if action == "read":
        try:
            return target.read_text(encoding="utf-8")
        except OSError as e:
            raise ToolError(
                f"file_io read failed: {type(e).__name__}: {e}",
                tool_name="file_io",
                context={"path": str(target)},
            ) from e

    # write
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return "ok"
    except OSError as e:
        raise ToolError(
            f"file_io write failed: {type(e).__name__}: {e}",
            tool_name="file_io",
            context={"path": str(target)},
        ) from e


__all__ = ["file_io"]
```

- [ ] **Step 5.7：实现 shell**

Create `packages/tools/src/tools/builtin/shell.py`：

```python
"""命令白名单内的 subprocess 工具。"""

from __future__ import annotations

import subprocess
from typing import Any

from common.errors import ToolError
from tools.registry import tool

_DEFAULT_TIMEOUT_S = 30.0


@tool(
    name="shell",
    description=(
        "执行外部命令。每次调用必须传 allowed_commands 白名单,argv[0] 不在白名单内会被拒。"
    ),
    require_approval=True,
    timeout_s=_DEFAULT_TIMEOUT_S,
)
def shell(argv: list[str], allowed_commands: list[str]) -> dict[str, Any]:
    """执行白名单内的命令。

    Args:
        argv: 完整命令行列表,argv[0] 是命令名。
        allowed_commands: 允许的命令名列表(只看 argv[0])。

    Returns:
        dict: {"returncode": int, "stdout": str, "stderr": str}
    """
    if not argv:
        raise ToolError("shell argv is empty", tool_name="shell")

    cmd = argv[0]
    if cmd not in allowed_commands:
        raise ToolError(
            f"shell command {cmd!r} not in allowed_commands {allowed_commands}",
            tool_name="shell",
            context={"command": cmd, "allowed": allowed_commands},
        )

    try:
        proc = subprocess.run(  # noqa: S603 - argv 已校验白名单
            argv,
            capture_output=True,
            text=True,
            timeout=_DEFAULT_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        raise ToolError(
            f"shell command timed out after {_DEFAULT_TIMEOUT_S}s",
            tool_name="shell",
            context={"argv": argv},
        ) from e
    except OSError as e:
        raise ToolError(
            f"shell exec failed: {type(e).__name__}: {e}",
            tool_name="shell",
            context={"argv": argv},
        ) from e

    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


__all__ = ["shell"]
```

- [ ] **Step 5.8：在 builtin `__init__.py` 加 re-export**

Replace `packages/tools/src/tools/builtin/__init__.py`：

```python
"""内置工具集合。"""

from __future__ import annotations

from .file_io import file_io
from .python_repl import python_repl
from .shell import shell
from .web_scrape import web_scrape
from .web_search import web_search

__all__ = ["file_io", "python_repl", "shell", "web_scrape", "web_search"]
```

- [ ] **Step 5.9：跑全部 builtin 测试确认通过**

```bash
uv run pytest packages/tools/tests/builtin -v
```

Expected：约 16 个测试全过(3 web_search + 3 web_scrape + 6 python_repl + 5 file_io + 5 shell)。

- [ ] **Step 5.10：跑包级覆盖率验证**

```bash
uv run pytest packages/tools --cov=tools --cov-report=term-missing
```

Expected：覆盖率 ≥ 85%(M2a 整体目标 80%,单包做高一些留缓冲)。

- [ ] **Step 5.11：lint + type**

```bash
uv run ruff check packages/tools
uv run mypy packages/tools
```

Expected：均通过。

- [ ] **Step 5.12：提交**

```bash
git add packages/tools/src/tools/builtin/python_repl.py packages/tools/src/tools/builtin/file_io.py packages/tools/src/tools/builtin/shell.py packages/tools/src/tools/builtin/__init__.py packages/tools/tests/builtin/test_python_repl.py packages/tools/tests/builtin/test_file_io.py packages/tools/tests/builtin/test_shell.py
git commit -m "feat(tools): 添加系统工具组（python_repl 安全简版 + file_io 路径白名单 + shell 命令白名单）"
```

---

## Task 6：创建 `packages/agent_core` 骨架

**Files:**
- Create: `packages/agent_core/pyproject.toml`
- Create: `packages/agent_core/README.md`
- Create: `packages/agent_core/src/agent_core/__init__.py`
- Create: `packages/agent_core/src/agent_core/py.typed`
- Create: `packages/agent_core/src/agent_core/patterns/__init__.py`
- Create: `packages/agent_core/tests/conftest.py`

- [ ] **Step 6.1：创建目录与 pyproject**

```bash
mkdir -p packages/agent_core/src/agent_core/patterns packages/agent_core/tests/patterns
```

Create `packages/agent_core/pyproject.toml`：

```toml
[project]
name = "agent-core"
version = "0.1.0"
description = "AgentTask Agent 抽象与运行时（state / events / runtime / checkpointer + 4 个 pattern 模板）"
readme = "README.md"
requires-python = ">=3.12,<3.13"
license = { text = "MIT" }
authors = [{ name = "AgentTask Author" }]
dependencies = [
    "common",
    "llm-providers",
    "tools",
    "pydantic>=2.9,<3",
    "langchain-core>=0.3.20,<0.4",
    "langgraph>=0.2.50,<0.4",
]

[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/agent_core"]

[tool.uv.sources]
common = { workspace = true }
llm-providers = { workspace = true }
tools = { workspace = true }
```

- [ ] **Step 6.2：写 README**

Create `packages/agent_core/README.md`：

````markdown
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
````

- [ ] **Step 6.3：写 `__init__.py` 占位**

Create `packages/agent_core/src/agent_core/__init__.py`：

```python
"""agent_core: Agent 抽象与运行时。

公开 API（M2a 期间逐 task 填充）。
"""

from __future__ import annotations

__version__ = "0.1.0"
```

Create `packages/agent_core/src/agent_core/py.typed`（空文件）。

Create `packages/agent_core/src/agent_core/patterns/__init__.py`（空文件，后续 task 填）。

Create `packages/agent_core/tests/conftest.py`：

```python
"""packages/agent_core 测试共用 fixtures。"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """每个测试前清空 AGENTTASK_ 前缀环境变量。"""
    for key in list(os.environ.keys()):
        if key.startswith(("AGENTTASK_", "OPENAI_", "ANTHROPIC_", "DEEPSEEK_")):
            monkeypatch.delenv(key, raising=False)
    yield


@pytest.fixture(autouse=True)
def _clear_tool_registry() -> Iterator[None]:
    """每个测试前后清空 tools 全局注册表(agent_core 测试会注册 fake 工具)。"""
    from tools import registry as _registry

    _registry._REGISTRY.clear()
    yield
    _registry._REGISTRY.clear()
```

- [ ] **Step 6.4：同步依赖**

```bash
uv sync --all-packages
```

Expected：解析并安装 `langgraph` 与传递依赖。`packages/agent_core` 作为 workspace 成员被识别。

- [ ] **Step 6.5：lint + type 验证骨架**

```bash
uv run ruff check packages/agent_core
uv run mypy packages/agent_core
```

Expected：均通过。

- [ ] **Step 6.6：提交**

```bash
git add packages/agent_core/pyproject.toml packages/agent_core/README.md packages/agent_core/src packages/agent_core/tests/conftest.py uv.lock
git commit -m "feat(agent-core): 创建 packages/agent_core 包骨架（依赖 common/llm_providers/tools/langgraph）"
```

---

## Task 7：`agent_core.events` —— 标准化事件层（TDD）

**Files:**
- Create: `packages/agent_core/tests/test_events.py`
- Create: `packages/agent_core/src/agent_core/events.py`

**设计要点（spec §8.4）：**
- `AgentEvent` 是 Pydantic 模型，前后端契约层。
- `type` 字段是字面量枚举：plan.* / subtask.* / tool.* / message.* / interrupt.* / cost.update / trace.link / error / done。
- `payload: dict[str, Any]` 给具体类型不同 schema；不强类型化（保持灵活性，前端按 type 分支）。
- 提供 `make_event(type, payload, *, node, trace_id)` 工厂函数（自动填 event_id / timestamp）。

- [ ] **Step 7.1：写失败的测试**

Create `packages/agent_core/tests/test_events.py`：

```python
"""AgentEvent 行为测试。"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from agent_core.events import AgentEvent, EventType, make_event


@pytest.mark.fast
def test_make_event_fills_id_and_timestamp() -> None:
    """make_event 自动生成 event_id（uuid4 字符串）与 timestamp（utc）。"""
    e = make_event(type="message.delta", payload={"content": "hi"}, node="agent")
    assert isinstance(e, AgentEvent)
    assert isinstance(e.event_id, str)
    assert len(e.event_id) >= 8
    assert isinstance(e.timestamp, datetime)
    assert e.timestamp.tzinfo == timezone.utc
    assert e.type == "message.delta"
    assert e.payload == {"content": "hi"}
    assert e.node == "agent"
    assert e.trace_id is None  # 未传时为 None


@pytest.mark.fast
def test_make_event_with_trace_id() -> None:
    """trace_id 应被保留。"""
    e = make_event(
        type="tool.called",
        payload={"tool_name": "x", "args": {}},
        node="tools",
        trace_id="t-123",
    )
    assert e.trace_id == "t-123"


@pytest.mark.fast
def test_event_unknown_type_raises() -> None:
    """type 不在 EventType 枚举内应被 pydantic 拒。"""
    with pytest.raises(ValueError):
        AgentEvent(
            event_id="x",
            type="not.real",  # type: ignore[arg-type]
            timestamp=datetime.now(tz=timezone.utc),
            payload={},
            node=None,
        )


@pytest.mark.fast
def test_event_serializes_to_json() -> None:
    """AgentEvent 必须支持 model_dump_json(供 SSE 推送)。"""
    e = make_event(type="done", payload={}, node=None)
    blob = e.model_dump_json()
    assert "done" in blob
    assert "event_id" in blob


@pytest.mark.fast
def test_event_type_enum_covers_spec() -> None:
    """EventType 必须覆盖 spec §8.4 列出的所有事件类型。"""
    required: set[str] = {
        "plan.created",
        "plan.updated",
        "subtask.started",
        "subtask.progress",
        "subtask.completed",
        "tool.called",
        "tool.result",
        "tool.error",
        "message.delta",
        "message.completed",
        "interrupt.requested",
        "interrupt.resolved",
        "cost.update",
        "trace.link",
        "error",
        "done",
    }
    actual: set[str] = {e.value for e in EventType}
    missing = required - actual
    assert not missing, f"EventType 缺少事件: {missing}"
```

- [ ] **Step 7.2：跑测试确认失败**

```bash
uv run pytest packages/agent_core/tests/test_events.py -v
```

Expected：ImportError。

- [ ] **Step 7.3：实现 events**

Create `packages/agent_core/src/agent_core/events.py`：

```python
"""标准化 Agent 事件层(spec §8.4)。

设计:
- AgentEvent 是前后端契约层,前端不需要懂 LangGraph 内部。
- type 用 str enum,可被 Pydantic 校验,也可作为 SSE 的 event 字段。
- payload 是 dict,具体 schema 由 type 决定(比如 plan.created 含 steps 列表;
  message.delta 含 content 字符串)。
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, enum.Enum):
    """所有支持的事件类型。"""

    PLAN_CREATED = "plan.created"
    PLAN_UPDATED = "plan.updated"
    SUBTASK_STARTED = "subtask.started"
    SUBTASK_PROGRESS = "subtask.progress"
    SUBTASK_COMPLETED = "subtask.completed"
    TOOL_CALLED = "tool.called"
    TOOL_RESULT = "tool.result"
    TOOL_ERROR = "tool.error"
    MESSAGE_DELTA = "message.delta"
    MESSAGE_COMPLETED = "message.completed"
    INTERRUPT_REQUESTED = "interrupt.requested"
    INTERRUPT_RESOLVED = "interrupt.resolved"
    COST_UPDATE = "cost.update"
    TRACE_LINK = "trace.link"
    ERROR = "error"
    DONE = "done"


class AgentEvent(BaseModel):
    """标准化 agent 事件。可序列化为 JSON 供 SSE 推送。"""

    event_id: str = Field(description="本次事件唯一 id(uuid4)")
    type: EventType = Field(description="事件类型")
    timestamp: datetime = Field(description="UTC 时间戳")
    payload: dict[str, Any] = Field(default_factory=dict)
    node: str | None = Field(default=None, description="发出事件的 node 名")
    trace_id: str | None = Field(default=None, description="跨调用的链路 id")


def make_event(
    *,
    type: str | EventType,
    payload: dict[str, Any] | None = None,
    node: str | None = None,
    trace_id: str | None = None,
) -> AgentEvent:
    """构造一个 AgentEvent,自动填 id 与时间戳。"""
    return AgentEvent(
        event_id=uuid.uuid4().hex,
        type=EventType(type) if not isinstance(type, EventType) else type,
        timestamp=datetime.now(tz=timezone.utc),
        payload=payload or {},
        node=node,
        trace_id=trace_id,
    )


__all__ = ["AgentEvent", "EventType", "make_event"]
```

- [ ] **Step 7.4：跑测试确认通过**

```bash
uv run pytest packages/agent_core/tests/test_events.py -v
```

Expected：5 个测试全过。

- [ ] **Step 7.5：lint + type**

```bash
uv run ruff check packages/agent_core
uv run mypy packages/agent_core
```

Expected：均通过。

- [ ] **Step 7.6：提交**

```bash
git add packages/agent_core/src/agent_core/events.py packages/agent_core/tests/test_events.py
git commit -m "feat(agent-core): 添加 AgentEvent 事件层（16 种事件类型 + Pydantic 模型）"
```

---

## Task 8：`agent_core.state` —— 状态定义（TDD）

**Files:**
- Create: `packages/agent_core/tests/test_state.py`
- Create: `packages/agent_core/src/agent_core/state.py`

**设计要点（spec §8.1）：**
- 用 `TypedDict` + `Annotated[T, reducer]`。
- `BaseAgentState`：`messages`（add_messages）+ `error`（last-write-wins）。
- `ReActState` extends BaseAgentState：仅 `messages`（直接复用 LangGraph 标准 ReAct 形态）。
- `PlanExecuteState`：`plan: list[str]` / `current_step: int` / `step_results: list[str]` / `final_answer: str`。
- `ReflectionState`：`task: str` / `draft: str` / `critique: str` / `final: str` / `iteration: int`。
- `ReflexionState`：`task: str` / `attempt: str` / `critique: str` / `experiences: list[str]` / `iteration: int`。

- [ ] **Step 8.1：写失败的测试**

Create `packages/agent_core/tests/test_state.py`：

```python
"""state 定义测试。"""

from __future__ import annotations

from typing import get_type_hints

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from agent_core.state import (
    BaseAgentState,
    PlanExecuteState,
    ReActState,
    ReflectionState,
    ReflexionState,
    add_unique,
)


@pytest.mark.fast
def test_base_agent_state_typed_dict() -> None:
    """BaseAgentState 是 TypedDict,可直接当 dict 用。"""
    s: BaseAgentState = {"messages": [], "error": None}
    assert s["messages"] == []
    assert s["error"] is None


@pytest.mark.fast
def test_react_state_inherits_messages() -> None:
    """ReActState 应包含 messages 字段。"""
    hints = get_type_hints(ReActState, include_extras=True)
    assert "messages" in hints


@pytest.mark.fast
def test_plan_execute_state_fields() -> None:
    """PlanExecuteState 必须含 plan / current_step / step_results / final_answer。"""
    hints = get_type_hints(PlanExecuteState, include_extras=True)
    for f in ("plan", "current_step", "step_results", "final_answer"):
        assert f in hints, f"PlanExecuteState 缺字段: {f}"


@pytest.mark.fast
def test_reflection_state_fields() -> None:
    """ReflectionState 必须含 task / draft / critique / final / iteration。"""
    hints = get_type_hints(ReflectionState, include_extras=True)
    for f in ("task", "draft", "critique", "final", "iteration"):
        assert f in hints, f"ReflectionState 缺字段: {f}"


@pytest.mark.fast
def test_reflexion_state_fields() -> None:
    """ReflexionState 必须含 task / attempt / critique / experiences / iteration。"""
    hints = get_type_hints(ReflexionState, include_extras=True)
    for f in ("task", "attempt", "critique", "experiences", "iteration"):
        assert f in hints, f"ReflexionState 缺字段: {f}"


@pytest.mark.fast
def test_add_unique_reducer_dedup() -> None:
    """add_unique reducer 合并两个 list 并按值去重(保持顺序)。"""
    a = ["x", "y"]
    b = ["y", "z"]
    assert add_unique(a, b) == ["x", "y", "z"]


@pytest.mark.fast
def test_add_unique_reducer_preserves_order() -> None:
    """add_unique 不改变首次出现顺序。"""
    a = ["b", "a"]
    b = ["a", "c", "b"]
    assert add_unique(a, b) == ["b", "a", "c"]


@pytest.mark.fast
def test_messages_reducer_is_add_messages() -> None:
    """ReActState.messages 应使用 LangGraph add_messages reducer(合并消息列表)。"""
    from langgraph.graph.message import add_messages

    hints = get_type_hints(ReActState, include_extras=True)
    metadata = getattr(hints["messages"], "__metadata__", ())
    assert add_messages in metadata, "messages 必须用 add_messages reducer"


@pytest.mark.fast
def test_messages_can_be_merged_via_reducer() -> None:
    """消息合并:add_messages 把两组消息按规则拼起来。"""
    from langgraph.graph.message import add_messages

    a: list[Any] = [HumanMessage(content="hi")]
    b: list[Any] = [AIMessage(content="hello")]
    merged = add_messages(a, b)
    assert len(merged) == 2
```

- [ ] **Step 8.2：跑测试确认失败**

```bash
uv run pytest packages/agent_core/tests/test_state.py -v
```

Expected：ImportError。

- [ ] **Step 8.3：实现 state**

Create `packages/agent_core/src/agent_core/state.py`：

```python
"""Agent state 定义(spec §8.1)。

设计:
- 用 TypedDict + Annotated[T, reducer]。LangGraph 用 reducer 合并并行 / sequential
  node 返回的 partial state。
- BaseAgentState 定义所有 agent 共用的最小字段(messages + error)。
- 每个 pattern 自己的 State 显式继承 BaseAgentState 并扩展业务字段。
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


def add_unique(left: list[str], right: list[str]) -> list[str]:
    """合并两个字符串列表,按首次出现顺序去重。"""
    seen: set[str] = set()
    out: list[str] = []
    for item in [*left, *right]:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


class BaseAgentState(TypedDict, total=False):
    """所有 agent 通用的最小 state。"""

    messages: Annotated[list[BaseMessage], add_messages]
    error: str | None


class ReActState(BaseAgentState):
    """ReAct 模式只需要消息流。"""


class PlanExecuteState(BaseAgentState):
    """Plan-and-Execute 模式。

    plan: 步骤字符串列表
    current_step: 下一个待执行步骤索引
    step_results: 每步的结果(按索引对齐)
    final_answer: 全部完成后的总结
    """

    plan: list[str]
    current_step: int
    step_results: Annotated[list[str], add_unique]
    final_answer: str


class ReflectionState(BaseAgentState):
    """Basic Reflection 模式。

    task: 用户原始任务
    draft: 当前草稿
    critique: 当轮 critic 反馈
    final: 终稿(满意后写入)
    iteration: 已迭代次数
    """

    task: str
    draft: str
    critique: str
    final: str
    iteration: int


class ReflexionState(BaseAgentState):
    """Reflexion 模式(带跨尝试的经验记忆)。

    task: 用户原始任务
    attempt: 本轮尝试结果
    critique: 当轮 critic 反馈
    experiences: 历次失败教训(跨 iteration 累积)
    iteration: 已尝试次数
    """

    task: str
    attempt: str
    critique: str
    experiences: Annotated[list[str], add_unique]
    iteration: int


__all__ = [
    "BaseAgentState",
    "PlanExecuteState",
    "ReActState",
    "ReflectionState",
    "ReflexionState",
    "add_unique",
]
```

- [ ] **Step 8.4：跑测试确认通过**

```bash
uv run pytest packages/agent_core/tests/test_state.py -v
```

Expected：9 个测试全过。

- [ ] **Step 8.5：lint + type**

```bash
uv run ruff check packages/agent_core
uv run mypy packages/agent_core
```

Expected：均通过。

- [ ] **Step 8.6：提交**

```bash
git add packages/agent_core/src/agent_core/state.py packages/agent_core/tests/test_state.py
git commit -m "feat(agent-core): 添加 state（BaseAgentState + 4 个 pattern 专用 state + add_unique reducer）"
```

---

## Task 9：`agent_core.checkpointer` —— 持久化工厂（TDD）

**Files:**
- Create: `packages/agent_core/tests/test_checkpointer.py`
- Create: `packages/agent_core/src/agent_core/checkpointer.py`

**设计要点：**
- `get_checkpointer(*, env=None)` 工厂：默认按 `Settings.app_env` 决定。
- M2a：`dev` → `MemorySaver`；`staging` / `prod` → 抛 `NotImplementedError("postgres saver added in M3")`。
- 提供显式参数 `env="dev"` 强制覆盖，便于测试。
- 返回类型 `BaseCheckpointSaver`。

- [ ] **Step 9.1：写失败的测试**

Create `packages/agent_core/tests/test_checkpointer.py`：

```python
"""checkpointer 工厂测试。"""

from __future__ import annotations

import pytest
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from agent_core.checkpointer import get_checkpointer


@pytest.mark.fast
def test_dev_returns_memory_saver() -> None:
    """env=dev 应返回 MemorySaver。"""
    cp = get_checkpointer(env="dev")
    assert isinstance(cp, MemorySaver)
    assert isinstance(cp, BaseCheckpointSaver)


@pytest.mark.fast
def test_default_uses_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """env=None 应读 Settings.app_env(默认 dev)。"""
    cp = get_checkpointer()
    assert isinstance(cp, MemorySaver)


@pytest.mark.fast
def test_prod_raises_not_implemented() -> None:
    """env=prod 在 M2a 应抛 NotImplementedError(M3 才接 Postgres)。"""
    with pytest.raises(NotImplementedError, match="M3"):
        get_checkpointer(env="prod")


@pytest.mark.fast
def test_staging_raises_not_implemented() -> None:
    """env=staging 同理。"""
    with pytest.raises(NotImplementedError, match="M3"):
        get_checkpointer(env="staging")


@pytest.mark.fast
def test_unknown_env_raises_config_error() -> None:
    """非法 env 字符串应抛 ConfigError。"""
    from common.errors import ConfigError

    with pytest.raises(ConfigError, match="env"):
        get_checkpointer(env="not-real-env")
```

- [ ] **Step 9.2：跑测试确认失败**

```bash
uv run pytest packages/agent_core/tests/test_checkpointer.py -v
```

Expected：ImportError。

- [ ] **Step 9.3：实现 checkpointer**

Create `packages/agent_core/src/agent_core/checkpointer.py`：

```python
"""LangGraph checkpointer 工厂。

M2a: 仅 dev 环境(MemorySaver)。
M3: 接 PostgresSaver(staging / prod)。
"""

from __future__ import annotations

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from common.config import AppEnv, get_settings
from common.errors import ConfigError


def get_checkpointer(*, env: str | None = None) -> BaseCheckpointSaver:
    """构造 checkpointer。

    Args:
        env: 显式指定环境(dev / staging / prod)。None 时读 Settings.app_env。

    Raises:
        ConfigError: env 不是合法 AppEnv。
        NotImplementedError: M2a 阶段 staging / prod 还没接 Postgres。
    """
    if env is None:
        env = get_settings(reload=True).app_env.value
    try:
        chosen = AppEnv(env)
    except ValueError as e:
        raise ConfigError(
            f"unknown env {env!r}; expected one of {[e.value for e in AppEnv]}",
            context={"env": env},
        ) from e

    if chosen is AppEnv.DEV:
        return MemorySaver()

    raise NotImplementedError(
        f"checkpointer for env={chosen.value!r} not yet implemented "
        "(PostgresSaver will be added in M3)"
    )


__all__ = ["get_checkpointer"]
```

- [ ] **Step 9.4：跑测试确认通过**

```bash
uv run pytest packages/agent_core/tests/test_checkpointer.py -v
```

Expected：5 个测试全过。

- [ ] **Step 9.5：lint + type**

```bash
uv run ruff check packages/agent_core
uv run mypy packages/agent_core
```

Expected：均通过。

- [ ] **Step 9.6：提交**

```bash
git add packages/agent_core/src/agent_core/checkpointer.py packages/agent_core/tests/test_checkpointer.py
git commit -m "feat(agent-core): 添加 checkpointer 工厂（dev=MemorySaver；staging/prod 留 M3 占位）"
```

---

## Task 10：`agent_core.interrupt` —— HITL 包装（TDD）

**Files:**
- Create: `packages/agent_core/tests/test_interrupt.py`
- Create: `packages/agent_core/src/agent_core/interrupt.py`

**设计要点：**
- LangGraph 0.2.x 提供 `interrupt()` 原语,我们包一层语义化 API:
  - `request_interrupt(reason: str, payload: dict) -> Any`：node 内调用,暂停 graph 并返回 caller 提供的 resume 值。
  - 包内输出对应的 `interrupt.requested` AgentEvent(由 runtime 监听,本 task 仅做 thin wrapper)。
- 测试用 `langgraph.types.interrupt` 的 mock(注入到 monkeypatch)。
- M4 第 12 章会基于此做完整 HITL UI;M2a 只验证 wrapper 调用了底层 interrupt。

- [ ] **Step 10.1：写失败的测试**

Create `packages/agent_core/tests/test_interrupt.py`：

```python
"""interrupt 包装测试。"""

from __future__ import annotations

from typing import Any

import pytest

from agent_core.interrupt import request_interrupt


@pytest.mark.fast
def test_request_interrupt_calls_langgraph_interrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """request_interrupt 应调用 langgraph.types.interrupt 并透传 payload。"""
    captured: dict[str, Any] = {}

    def fake_interrupt(value: dict[str, Any]) -> str:
        captured.update(value)
        return "resumed-with-foo"

    monkeypatch.setattr("agent_core.interrupt._interrupt", fake_interrupt)

    result = request_interrupt(
        reason="approve_tool_call",
        payload={"tool": "shell", "argv": ["rm", "-rf", "/"]},
    )
    assert result == "resumed-with-foo"
    assert captured["reason"] == "approve_tool_call"
    assert captured["payload"] == {"tool": "shell", "argv": ["rm", "-rf", "/"]}


@pytest.mark.fast
def test_request_interrupt_default_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """payload=None 时应传 {} 给底层。"""
    captured: dict[str, Any] = {}

    def fake_interrupt(value: dict[str, Any]) -> Any:
        captured.update(value)
        return None

    monkeypatch.setattr("agent_core.interrupt._interrupt", fake_interrupt)

    request_interrupt(reason="confirm")
    assert captured["payload"] == {}
```

- [ ] **Step 10.2：跑测试确认失败**

```bash
uv run pytest packages/agent_core/tests/test_interrupt.py -v
```

Expected：ImportError。

- [ ] **Step 10.3：实现 interrupt**

Create `packages/agent_core/src/agent_core/interrupt.py`：

```python
"""HITL interrupt 包装。

LangGraph 0.2.x 提供 `langgraph.types.interrupt` 原语,允许 node 暂停 graph
并把控制权交还 caller,等 caller 提供 resume 值后再继续。

本模块在它之上加一层语义化 API,统一 payload 结构(便于前端按 reason 分类
渲染审批 UI)。M4 第 12 章会接前端 SSE + Vercel AI SDK。
"""

from __future__ import annotations

from typing import Any

from langgraph.types import interrupt as _interrupt


def request_interrupt(
    *,
    reason: str,
    payload: dict[str, Any] | None = None,
) -> Any:
    """暂停 graph,把 reason + payload 交给 caller 决定如何 resume。

    用法:
        @node
        def maybe_run_tool(state):
            decision = request_interrupt(
                reason="approve_tool_call",
                payload={"tool": tool_name, "args": args},
            )
            if decision != "approved":
                return {"error": "user rejected"}
            ...

    Args:
        reason: 中断语义("approve_tool_call" / "edit_plan" / ...)。
        payload: 给前端渲染需要的上下文。

    Returns:
        Any: caller 通过 Command(resume=...) 传入的值。
    """
    return _interrupt({"reason": reason, "payload": payload or {}})


__all__ = ["request_interrupt"]
```

- [ ] **Step 10.4：跑测试确认通过**

```bash
uv run pytest packages/agent_core/tests/test_interrupt.py -v
```

Expected：2 个测试全过。

- [ ] **Step 10.5：lint + type**

```bash
uv run ruff check packages/agent_core
uv run mypy packages/agent_core
```

Expected：均通过。

- [ ] **Step 10.6：提交**

```bash
git add packages/agent_core/src/agent_core/interrupt.py packages/agent_core/tests/test_interrupt.py
git commit -m "feat(agent-core): 添加 request_interrupt HITL 包装（LangGraph interrupt 之上的语义层）"
```

---

## Task 11：`agent_core.runtime` —— Agent 运行时（TDD）

**Files:**
- Create: `packages/agent_core/tests/test_runtime.py`
- Create: `packages/agent_core/src/agent_core/runtime.py`
- Modify: `packages/agent_core/src/agent_core/__init__.py`（re-export）

**设计要点：**
- `AgentRuntime(graph, *, checkpointer=None, cost_tracker=None)`。
- `.invoke(input, *, thread_id="default")`：同步执行,返回最终 state。
- `.astream(input, *, thread_id)`：返回 `AsyncIterator[AgentEvent]`,把 LangGraph stream 事件映射到我们的 AgentEvent。
- 错误兜底:graph 中任何未捕获异常 → 写 `state["error"]` + emit `error` event + emit `done` event。
- M2a 的 astream **简版**:只把 message.delta / done / error 三类事件映射出来。完整事件映射(plan.* / subtask.* / tool.* 等)在 M4 第 12 章扩展。

- [ ] **Step 11.1：写失败的测试**

Create `packages/agent_core/tests/test_runtime.py`：

```python
"""AgentRuntime 测试。"""

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from agent_core.events import EventType
from agent_core.runtime import AgentRuntime
from agent_core.state import BaseAgentState


def _build_simple_graph() -> Any:
    """一个 1-node graph: 加一条 AI 消息后退出。"""

    def echo_node(state: BaseAgentState) -> dict[str, Any]:
        last = state["messages"][-1]
        return {"messages": [AIMessage(content=f"echo: {last.content}")]}

    g = StateGraph(BaseAgentState)
    g.add_node("echo", echo_node)
    g.add_edge(START, "echo")
    g.add_edge("echo", END)
    return g.compile()


def _build_failing_graph() -> Any:
    def boom(state: BaseAgentState) -> dict[str, Any]:
        raise RuntimeError("kaboom")

    g = StateGraph(BaseAgentState)
    g.add_node("boom", boom)
    g.add_edge(START, "boom")
    g.add_edge("boom", END)
    return g.compile()


@pytest.mark.fast
def test_runtime_invoke_returns_final_state() -> None:
    """invoke 应返回 graph 终态。"""
    runtime = AgentRuntime(_build_simple_graph())
    out = runtime.invoke({"messages": [HumanMessage(content="hi")]})
    assert isinstance(out, dict)
    msgs = out["messages"]
    assert any("echo: hi" in str(m.content) for m in msgs)


@pytest.mark.fast
def test_runtime_invoke_wraps_runtime_error() -> None:
    """graph 抛错时 invoke 应在返回 state 里写 error,而不是炸出去。"""
    runtime = AgentRuntime(_build_failing_graph())
    out = runtime.invoke({"messages": [HumanMessage(content="x")]})
    assert out.get("error")
    assert "kaboom" in out["error"]


@pytest.mark.fast
async def test_runtime_astream_emits_done() -> None:
    """astream 至少 emit 一条 done 事件。"""
    runtime = AgentRuntime(_build_simple_graph())
    events = [
        e
        async for e in runtime.astream({"messages": [HumanMessage(content="hi")]})
    ]
    assert any(e.type is EventType.DONE for e in events)


@pytest.mark.fast
async def test_runtime_astream_emits_error_then_done() -> None:
    """graph 抛错时 astream 应 emit 一条 error + 一条 done。"""
    runtime = AgentRuntime(_build_failing_graph())
    events = [
        e
        async for e in runtime.astream({"messages": [HumanMessage(content="x")]})
    ]
    types = [e.type for e in events]
    assert EventType.ERROR in types
    assert EventType.DONE in types
    err_event = next(e for e in events if e.type is EventType.ERROR)
    assert "kaboom" in err_event.payload.get("message", "")


@pytest.mark.fast
def test_runtime_supports_thread_id_via_checkpointer() -> None:
    """配 checkpointer 时,同一 thread_id 第二次 invoke 应能续上之前的 state。"""
    from agent_core.checkpointer import get_checkpointer

    runtime = AgentRuntime(
        _build_simple_graph(),
        checkpointer=get_checkpointer(env="dev"),
    )
    out1 = runtime.invoke({"messages": [HumanMessage(content="a")]}, thread_id="t1")
    out2 = runtime.invoke({"messages": [HumanMessage(content="b")]}, thread_id="t1")
    # 第二次输出应包含两轮消息(a 的 echo + b 的 echo)
    assert len(out2["messages"]) >= 4  # a, echo:a, b, echo:b
```

- [ ] **Step 11.2：跑测试确认失败**

```bash
uv run pytest packages/agent_core/tests/test_runtime.py -v
```

Expected：ImportError。

- [ ] **Step 11.3：实现 runtime**

Create `packages/agent_core/src/agent_core/runtime.py`：

```python
"""Agent 运行时。

把 LangGraph CompiledStateGraph 包成统一接口:
- invoke: 同步,返回终态(含 error 兜底)。
- astream: 异步,产出 AgentEvent 流(M2a 简版,M4 扩展)。
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from common.cost import CostTracker

from .events import AgentEvent, EventType, make_event


class AgentRuntime:
    """统一 agent 运行入口。

    Args:
        graph: 已 compile 的 StateGraph。
        checkpointer: 可选,持久化 state(同 thread_id 续传)。
        cost_tracker: 可选,M2a 暂未消费,留接口给 M4 cost 事件。
    """

    def __init__(
        self,
        graph: CompiledStateGraph,
        *,
        checkpointer: BaseCheckpointSaver | None = None,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        self._graph = (
            graph.with_config({"checkpointer": checkpointer})
            if checkpointer is not None
            else graph
        )
        # 重新 compile 以注入 checkpointer
        if checkpointer is not None:
            # LangGraph 要在 compile 时传 checkpointer,这里我们用 builder 重建
            # 注意:graph 已经 compile 过,无法再注入 checkpointer。
            # 实际用法:caller 应传未 compile 的 builder 或 compile 时自己带 checkpointer。
            # 简化策略:直接保存 checkpointer,在 invoke 时通过 config 传入。
            self._graph = graph
        else:
            self._graph = graph
        self._checkpointer = checkpointer
        self._cost_tracker = cost_tracker

    def _config_for(self, thread_id: str) -> dict[str, Any]:
        cfg: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
        return cfg

    def invoke(
        self,
        input: dict[str, Any],
        *,
        thread_id: str = "default",
    ) -> dict[str, Any]:
        """同步执行 graph,异常被捕获并写入 state.error。"""
        try:
            return dict(
                self._graph.invoke(input, config=self._config_for(thread_id))
            )
        except Exception as e:  # noqa: BLE001
            return {
                **input,
                "error": f"{type(e).__name__}: {e}",
            }

    async def astream(
        self,
        input: dict[str, Any],
        *,
        thread_id: str = "default",
    ) -> AsyncIterator[AgentEvent]:
        """异步执行,产出标准化事件流。

        M2a 简版:
        - 每个 node 执行完后 emit 一条 message.delta(若产生新 AIMessage)。
        - 全部完成 emit 一条 done。
        - 异常 emit 一条 error + 一条 done。
        """
        try:
            async for chunk in self._graph.astream(
                input, config=self._config_for(thread_id), stream_mode="updates"
            ):
                # chunk: dict[node_name, dict[str, Any]] 形如
                #   {"echo": {"messages": [AIMessage(...)]}}
                for node_name, partial_state in chunk.items():
                    msgs = partial_state.get("messages") if isinstance(partial_state, dict) else None
                    if msgs:
                        for m in msgs:
                            if isinstance(m, AIMessage):
                                yield make_event(
                                    type=EventType.MESSAGE_DELTA,
                                    payload={"content": str(m.content)},
                                    node=node_name,
                                )
        except Exception as e:  # noqa: BLE001
            yield make_event(
                type=EventType.ERROR,
                payload={"message": f"{type(e).__name__}: {e}"},
            )
        yield make_event(type=EventType.DONE)


__all__ = ["AgentRuntime"]
```

> **Note for implementer:** 上面 `__init__` 写了两段保留 checkpointer 的代码用于说明,实际只需要保存 `self._checkpointer = checkpointer` 一句;LangGraph 0.2.50+ 期望 caller 在 compile 时自己传 checkpointer。最终建议把 `__init__` 简化为:
> ```python
> def __init__(self, graph, *, checkpointer=None, cost_tracker=None):
>     self._graph = graph
>     self._checkpointer = checkpointer
>     self._cost_tracker = cost_tracker
> ```
> 并要求 caller 自己 `graph = builder.compile(checkpointer=cp)`。测试 `test_runtime_supports_thread_id_via_checkpointer` 要随之改成传 compile 时已含 checkpointer 的 graph。

- [ ] **Step 11.4：调整测试以匹配最终接口**

按上面 Note 简化 runtime 后,把 `test_runtime_supports_thread_id_via_checkpointer` 改成:

```python
@pytest.mark.fast
def test_runtime_supports_thread_id_via_checkpointer() -> None:
    """配 checkpointer 时,同一 thread_id 第二次 invoke 应能续上之前的 state。"""
    from agent_core.checkpointer import get_checkpointer

    cp = get_checkpointer(env="dev")

    def echo_node(state: BaseAgentState) -> dict[str, Any]:
        last = state["messages"][-1]
        return {"messages": [AIMessage(content=f"echo: {last.content}")]}

    g = StateGraph(BaseAgentState)
    g.add_node("echo", echo_node)
    g.add_edge(START, "echo")
    g.add_edge("echo", END)
    graph = g.compile(checkpointer=cp)

    runtime = AgentRuntime(graph, checkpointer=cp)
    out1 = runtime.invoke(
        {"messages": [HumanMessage(content="a")]}, thread_id="t1"
    )
    out2 = runtime.invoke(
        {"messages": [HumanMessage(content="b")]}, thread_id="t1"
    )
    assert len(out2["messages"]) >= 4
```

并把 runtime 的 `__init__` 简化为:

```python
def __init__(
    self,
    graph: CompiledStateGraph,
    *,
    checkpointer: BaseCheckpointSaver | None = None,
    cost_tracker: CostTracker | None = None,
) -> None:
    self._graph = graph
    self._checkpointer = checkpointer
    self._cost_tracker = cost_tracker
```

- [ ] **Step 11.5：在 `__init__.py` re-export**

Replace `packages/agent_core/src/agent_core/__init__.py`：

```python
"""agent_core: Agent 抽象与运行时。

公开 API:
- AgentEvent / EventType / make_event: 标准化事件
- BaseAgentState / ReActState / PlanExecuteState / ReflectionState / ReflexionState: 状态
- AgentRuntime: 运行时
- get_checkpointer: 持久化工厂
- request_interrupt: HITL 入口

具体 build_<pattern>_graph 在 patterns 子模块,后续 task 加入。
"""

from __future__ import annotations

from .checkpointer import get_checkpointer
from .events import AgentEvent, EventType, make_event
from .interrupt import request_interrupt
from .runtime import AgentRuntime
from .state import (
    BaseAgentState,
    PlanExecuteState,
    ReActState,
    ReflectionState,
    ReflexionState,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "AgentEvent",
    "AgentRuntime",
    "BaseAgentState",
    "EventType",
    "PlanExecuteState",
    "ReActState",
    "ReflectionState",
    "ReflexionState",
    "get_checkpointer",
    "make_event",
    "request_interrupt",
]
```

- [ ] **Step 11.6：跑测试确认通过**

```bash
uv run pytest packages/agent_core/tests/test_runtime.py -v
```

Expected：5 个测试全过。

- [ ] **Step 11.7：lint + type**

```bash
uv run ruff check packages/agent_core
uv run mypy packages/agent_core
```

Expected：均通过。

- [ ] **Step 11.8：提交**

```bash
git add packages/agent_core/src/agent_core/runtime.py packages/agent_core/src/agent_core/__init__.py packages/agent_core/tests/test_runtime.py
git commit -m "feat(agent-core): 添加 AgentRuntime（invoke + astream + 错误兜底）"
```

---

## Task 12：`agent_core.patterns.react` —— ReAct 模式（TDD）

**Files:**
- Create: `packages/agent_core/tests/patterns/__init__.py`
- Create: `packages/agent_core/tests/patterns/test_react.py`
- Create: `packages/agent_core/src/agent_core/patterns/react.py`
- Modify: `packages/agent_core/src/agent_core/patterns/__init__.py`

**设计要点：**
- `build_react_graph(*, llm: BaseChatModel, tools: list[BaseTool], system_prompt: str | None = None) -> CompiledStateGraph` 工厂函数。
- 用 LangGraph 标准 ReAct 形态：`agent` node → 条件边（有 tool_calls 走 `tools` node 后回 `agent`，无则结束）。
- `tools` node 用 LangGraph 内置 `ToolNode`（已正确处理 ToolError）。
- `agent` node 调 `llm.bind_tools(tools).invoke(messages)`。
- 测试用 `FakeListChatModel` + 一个简单加法 tool 跑通"agent 想用工具 → 调 tool → 拿结果 → 给最终答"完整循环。

- [ ] **Step 12.1：写失败的测试**

Create `packages/agent_core/tests/patterns/__init__.py`（空文件）。

Create `packages/agent_core/tests/patterns/test_react.py`：

```python
"""ReAct 模式 graph 测试(用 fake LLM,完全本地)。"""

from __future__ import annotations

from typing import Any

import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.messages import AIMessage, HumanMessage

from agent_core import AgentRuntime
from agent_core.patterns.react import build_react_graph
from tools import tool


def _make_fake_llm_with_tool_call(tool_args: dict[str, Any]) -> Any:
    """构造一个 fake LLM:第一轮回 tool_call,第二轮回最终答。

    FakeListChatModel 不能直接发 tool_calls,这里用 monkey 实现:
    继承一个最小 LLM,override invoke 返回带 tool_calls 的 AIMessage。
    """
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.outputs import ChatGeneration, ChatResult

    class _ScriptedLLM(BaseChatModel):
        responses: list[Any] = []
        idx: int = 0

        @property
        def _llm_type(self) -> str:
            return "scripted"

        def bind_tools(self, tools: list[Any]) -> Any:
            return self

        def _generate(  # type: ignore[override]
            self,
            messages: list[Any],
            stop: list[str] | None = None,
            run_manager: Any = None,
            **kwargs: Any,
        ) -> ChatResult:
            msg = self.responses[self.idx]
            self.idx += 1
            return ChatResult(generations=[ChatGeneration(message=msg)])

    first = AIMessage(
        content="",
        tool_calls=[{"name": "add", "args": tool_args, "id": "call_1"}],
    )
    final = AIMessage(content="结果是 5。")
    return _ScriptedLLM(responses=[first, final])


@pytest.mark.fast
def test_react_calls_tool_then_answers() -> None:
    """ReAct: agent 决定调 add,调完拿结果给最终答。"""

    @tool(name="add", description="加法")
    def add(a: int, b: int) -> int:
        return a + b

    llm = _make_fake_llm_with_tool_call({"a": 2, "b": 3})
    graph = build_react_graph(llm=llm, tools=[add])
    runtime = AgentRuntime(graph)

    out = runtime.invoke({"messages": [HumanMessage(content="算 2+3")]})
    msgs = out["messages"]
    # 应包含: user / ai_with_tool_call / tool_result / ai_final
    assert len(msgs) >= 4
    final = msgs[-1]
    assert "5" in str(final.content)


@pytest.mark.fast
def test_react_no_tool_call_terminates_immediately() -> None:
    """LLM 直接给答(无 tool_call)应立即结束。"""

    llm = FakeListChatModel(responses=["直接给答"])
    graph = build_react_graph(llm=llm, tools=[])
    runtime = AgentRuntime(graph)

    out = runtime.invoke({"messages": [HumanMessage(content="hi")]})
    final = out["messages"][-1]
    assert "直接给答" in str(final.content)


@pytest.mark.fast
def test_react_system_prompt_prepended() -> None:
    """system_prompt 应作为 SystemMessage 加到对话最前。"""
    from langchain_core.messages import SystemMessage

    llm = FakeListChatModel(responses=["ok"])
    graph = build_react_graph(
        llm=llm, tools=[], system_prompt="你是研究助手。"
    )
    runtime = AgentRuntime(graph)

    out = runtime.invoke({"messages": [HumanMessage(content="hi")]})
    assert any(
        isinstance(m, SystemMessage) and "研究助手" in str(m.content)
        for m in out["messages"]
    )
```

- [ ] **Step 12.2：跑测试确认失败**

```bash
uv run pytest packages/agent_core/tests/patterns/test_react.py -v
```

Expected：ImportError。

- [ ] **Step 12.3：实现 react pattern**

Create `packages/agent_core/src/agent_core/patterns/react.py`：

```python
"""ReAct 模式 graph 工厂。

形态:
    START → agent → (有 tool_calls?) → tools → agent → ... → END

agent node 调 llm.bind_tools(tools).invoke(messages),
tools node 用 LangGraph ToolNode(自动处理 ToolError)。
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from ..state import ReActState


def _should_continue(state: ReActState) -> str:
    """有 tool_calls → 'tools',否则 → END。"""
    last = state["messages"][-1]
    tool_calls = getattr(last, "tool_calls", None)
    if tool_calls:
        return "tools"
    return END


def build_react_graph(
    *,
    llm: BaseChatModel,
    tools: list[BaseTool],
    system_prompt: str | None = None,
) -> CompiledStateGraph:
    """构造 ReAct 模式的 graph(已 compile,未带 checkpointer)。

    Args:
        llm: 任意 LangChain BaseChatModel(实测应支持 tool calling)。
        tools: BaseTool 列表(我们的 Tool 是 BaseTool 子类,直接传)。
        system_prompt: 可选系统提示。
    """
    bound_llm = llm.bind_tools(tools) if tools else llm

    def agent_node(state: ReActState) -> dict[str, Any]:
        msgs = list(state["messages"])
        if system_prompt and not any(
            isinstance(m, SystemMessage) for m in msgs
        ):
            msgs = [SystemMessage(content=system_prompt), *msgs]
        response = bound_llm.invoke(msgs)
        # 如果原始 messages 没有 system,我们补的 system 也要返回(让 reducer 合并入 state)
        new_msgs: list[Any] = []
        if system_prompt and not any(
            isinstance(m, SystemMessage) for m in state["messages"]
        ):
            new_msgs.append(SystemMessage(content=system_prompt))
        new_msgs.append(response)
        return {"messages": new_msgs}

    builder = StateGraph(ReActState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", _should_continue, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")
    return builder.compile()


__all__ = ["build_react_graph"]
```

- [ ] **Step 12.4：在 patterns `__init__.py` re-export**

Replace `packages/agent_core/src/agent_core/patterns/__init__.py`：

```python
"""模式模板集合。"""

from __future__ import annotations

from .react import build_react_graph

__all__ = ["build_react_graph"]
```

- [ ] **Step 12.5：跑测试确认通过**

```bash
uv run pytest packages/agent_core/tests/patterns/test_react.py -v
```

Expected：3 个测试全过。

- [ ] **Step 12.6：lint + type**

```bash
uv run ruff check packages/agent_core
uv run mypy packages/agent_core
```

Expected：均通过。

- [ ] **Step 12.7：提交**

```bash
git add packages/agent_core/src/agent_core/patterns/react.py packages/agent_core/src/agent_core/patterns/__init__.py packages/agent_core/tests/patterns/__init__.py packages/agent_core/tests/patterns/test_react.py
git commit -m "feat(agent-core): 添加 ReAct 模式 graph（agent ↔ tools 循环）"
```

---

## Task 13：`agent_core.patterns.plan_execute` —— Plan-Execute 模式（TDD）

**Files:**
- Create: `packages/agent_core/tests/patterns/test_plan_execute.py`
- Create: `packages/agent_core/src/agent_core/patterns/plan_execute.py`
- Modify: `packages/agent_core/src/agent_core/patterns/__init__.py`

**设计要点：**
- `build_plan_execute_graph(*, planner_llm, executor_llm, max_steps=10)`。
- 形态：START → planner（出 list[str] 步骤）→ executor（按 current_step 执行单步）→ 条件（current_step < len(plan)？回 executor : 走 finalize）→ finalize（合成最终回答）→ END。
- planner / executor / finalize 都是单 LLM 调用，prompt 简单。
- planner 输出用 `with_structured_output`（M1 已可用 LangChain 标准 API）解析成 `list[str]`。

- [ ] **Step 13.1：写失败的测试**

Create `packages/agent_core/tests/patterns/test_plan_execute.py`：

```python
"""Plan-Execute 模式 graph 测试。"""

from __future__ import annotations

from typing import Any

import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.messages import HumanMessage

from agent_core import AgentRuntime
from agent_core.patterns.plan_execute import build_plan_execute_graph


def _scripted_llm(responses: list[str]) -> Any:
    """FakeListChatModel 在每次 invoke 取下一个字符串作为 AI 响应。"""
    return FakeListChatModel(responses=responses)


@pytest.mark.fast
def test_plan_execute_runs_all_steps() -> None:
    """planner 出 3 步 → executor 各执行一次 → finalize 合成。"""
    planner_llm = _scripted_llm(
        responses=[
            "1. 查找资料\n2. 整理要点\n3. 撰写答案"
        ]
    )
    executor_llm = _scripted_llm(
        responses=["资料: A B C", "要点: A>B", "草稿"]
    )
    finalizer_llm = _scripted_llm(responses=["最终答: A 优于 B"])

    graph = build_plan_execute_graph(
        planner_llm=planner_llm,
        executor_llm=executor_llm,
        finalizer_llm=finalizer_llm,
    )
    runtime = AgentRuntime(graph)
    out = runtime.invoke(
        {"messages": [HumanMessage(content="比较 A 和 B")]}
    )

    assert out.get("plan")
    assert len(out["plan"]) == 3
    assert len(out["step_results"]) == 3
    assert "最终答" in out["final_answer"]


@pytest.mark.fast
def test_plan_execute_respects_max_steps() -> None:
    """planner 出 100 步,设置 max_steps=2 → 最多执行 2 步后强制 finalize。"""
    big_plan = "\n".join(f"{i}. step{i}" for i in range(1, 101))
    planner_llm = _scripted_llm(responses=[big_plan])
    executor_llm = _scripted_llm(responses=["r1", "r2", "r3"])
    finalizer_llm = _scripted_llm(responses=["truncated"])

    graph = build_plan_execute_graph(
        planner_llm=planner_llm,
        executor_llm=executor_llm,
        finalizer_llm=finalizer_llm,
        max_steps=2,
    )
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="x")]})

    assert len(out["step_results"]) == 2


@pytest.mark.fast
def test_plan_execute_empty_plan_goes_to_finalize() -> None:
    """planner 没出步骤 → 直接 finalize。"""
    planner_llm = _scripted_llm(responses=[""])
    executor_llm = _scripted_llm(responses=[])
    finalizer_llm = _scripted_llm(responses=["nothing to do"])

    graph = build_plan_execute_graph(
        planner_llm=planner_llm,
        executor_llm=executor_llm,
        finalizer_llm=finalizer_llm,
    )
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="trivial")]})

    assert out["plan"] == []
    assert out["step_results"] == []
    assert "nothing" in out["final_answer"]
```

- [ ] **Step 13.2：跑测试确认失败**

```bash
uv run pytest packages/agent_core/tests/patterns/test_plan_execute.py -v
```

Expected：ImportError。

- [ ] **Step 13.3：实现 plan_execute**

Create `packages/agent_core/src/agent_core/patterns/plan_execute.py`：

```python
"""Plan-Execute 模式 graph 工厂。

形态:
    START → planner → executor → (still steps?) → executor → ... → finalize → END

planner: 把用户问题拆成 list[str] 步骤。
executor: 按 current_step 执行单步,把结果写入 step_results。
finalize: 用 plan + step_results 合成最终答。
"""

from __future__ import annotations

import re
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ..state import PlanExecuteState

_PLANNER_SYSTEM = (
    "你是任务分解专家。把用户的问题拆成 3-7 个原子步骤,"
    "每步一行,以 '1. ' / '2. ' / ... 开头。如果问题不需要分步,直接输出空。"
)
_EXECUTOR_SYSTEM = (
    "你正在执行一个步骤。已知整体计划与已执行结果。"
    "只输出当前步骤的产出,不要重复整体计划。"
)
_FINALIZER_SYSTEM = (
    "你是总结员。基于计划与每步结果,给出最终答复给用户。"
)


def _parse_plan(text: str) -> list[str]:
    """从 LLM 输出里抽出步骤行。空输入返回 []。"""
    if not text.strip():
        return []
    steps: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^\s*(\d+)[\.\)]\s*(.+)$", line)
        if m:
            steps.append(m.group(2).strip())
    return steps


def build_plan_execute_graph(
    *,
    planner_llm: BaseChatModel,
    executor_llm: BaseChatModel,
    finalizer_llm: BaseChatModel,
    max_steps: int = 10,
) -> CompiledStateGraph:
    """构造 Plan-Execute graph(已 compile)。

    Args:
        planner_llm / executor_llm / finalizer_llm: 三个角色 LLM(可同一实例)。
        max_steps: 安全上限,防止 planner 出过多步骤把 token 烧光。
    """

    def planner_node(state: PlanExecuteState) -> dict[str, Any]:
        msgs = [SystemMessage(content=_PLANNER_SYSTEM), *state["messages"]]
        out = planner_llm.invoke(msgs)
        plan = _parse_plan(str(out.content))[:max_steps]
        return {"plan": plan, "current_step": 0, "step_results": []}

    def executor_node(state: PlanExecuteState) -> dict[str, Any]:
        idx = state.get("current_step", 0)
        plan = state.get("plan", [])
        if idx >= len(plan) or idx >= max_steps:
            return {"current_step": idx}
        step = plan[idx]
        already = state.get("step_results", [])
        context = "\n".join(
            f"步骤 {i + 1}: {plan[i]}\n结果: {r}"
            for i, r in enumerate(already)
        )
        prompt = (
            f"整体计划:\n"
            + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(plan))
            + f"\n\n已执行:\n{context}\n\n现在执行第 {idx + 1} 步: {step}"
        )
        out = executor_llm.invoke(
            [SystemMessage(content=_EXECUTOR_SYSTEM), HumanMessage(content=prompt)]
        )
        return {
            "step_results": [str(out.content)],
            "current_step": idx + 1,
        }

    def finalizer_node(state: PlanExecuteState) -> dict[str, Any]:
        plan = state.get("plan", [])
        results = state.get("step_results", [])
        body = "\n".join(
            f"步骤 {i + 1}: {plan[i] if i < len(plan) else ''}\n结果: {r}"
            for i, r in enumerate(results)
        ) or "(无步骤)"
        prompt = f"原始问题对话见上文。计划与结果:\n{body}\n\n请给出最终答复。"
        msgs = [
            SystemMessage(content=_FINALIZER_SYSTEM),
            *state["messages"],
            HumanMessage(content=prompt),
        ]
        out = finalizer_llm.invoke(msgs)
        return {"final_answer": str(out.content)}

    def _should_continue(state: PlanExecuteState) -> str:
        idx = state.get("current_step", 0)
        plan = state.get("plan", [])
        if idx < len(plan) and idx < max_steps:
            return "executor"
        return "finalizer"

    builder = StateGraph(PlanExecuteState)
    builder.add_node("planner", planner_node)
    builder.add_node("executor", executor_node)
    builder.add_node("finalizer", finalizer_node)
    builder.add_edge(START, "planner")
    builder.add_conditional_edges(
        "planner",
        _should_continue,
        {"executor": "executor", "finalizer": "finalizer"},
    )
    builder.add_conditional_edges(
        "executor",
        _should_continue,
        {"executor": "executor", "finalizer": "finalizer"},
    )
    builder.add_edge("finalizer", END)
    return builder.compile()


__all__ = ["build_plan_execute_graph"]
```

- [ ] **Step 13.4：在 patterns `__init__.py` 加 re-export**

Replace `packages/agent_core/src/agent_core/patterns/__init__.py`：

```python
"""模式模板集合。"""

from __future__ import annotations

from .plan_execute import build_plan_execute_graph
from .react import build_react_graph

__all__ = ["build_plan_execute_graph", "build_react_graph"]
```

- [ ] **Step 13.5：跑测试确认通过**

```bash
uv run pytest packages/agent_core/tests/patterns/test_plan_execute.py -v
```

Expected：3 个测试全过。

- [ ] **Step 13.6：lint + type**

```bash
uv run ruff check packages/agent_core
uv run mypy packages/agent_core
```

Expected：均通过。

- [ ] **Step 13.7：提交**

```bash
git add packages/agent_core/src/agent_core/patterns/plan_execute.py packages/agent_core/src/agent_core/patterns/__init__.py packages/agent_core/tests/patterns/test_plan_execute.py
git commit -m "feat(agent-core): 添加 Plan-Execute 模式 graph（planner → executor* → finalizer）"
```

---

## Task 14：`agent_core.patterns.reflection` —— Basic Reflection 模式（TDD）

**Files:**
- Create: `packages/agent_core/tests/patterns/test_reflection.py`
- Create: `packages/agent_core/src/agent_core/patterns/reflection.py`
- Modify: `packages/agent_core/src/agent_core/patterns/__init__.py`

**设计要点：**
- `build_reflection_graph(*, generator_llm, critic_llm, max_iterations=3, accept_marker="ACCEPT")`。
- 形态：START → generate → critic → 条件（critique 含 ACCEPT 或达到 max_iterations？走 finalize : 回 generate）→ finalize → END。
- generate node 第一次基于 task 出 draft；之后基于 task + 上一轮 draft + critique 出新 draft。
- critic node 输出 critique 字符串，结尾 `ACCEPT` 表示满意。

- [ ] **Step 14.1：写失败的测试**

Create `packages/agent_core/tests/patterns/test_reflection.py`：

```python
"""Reflection 模式 graph 测试。"""

from __future__ import annotations

import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.messages import HumanMessage

from agent_core import AgentRuntime
from agent_core.patterns.reflection import build_reflection_graph


@pytest.mark.fast
def test_reflection_accepts_when_critic_signals_accept() -> None:
    """critic 第一轮直接 ACCEPT → 一轮就结束。"""
    gen = FakeListChatModel(responses=["draft v1", "draft v2"])
    crit = FakeListChatModel(responses=["不错。ACCEPT"])
    graph = build_reflection_graph(
        generator_llm=gen, critic_llm=crit, max_iterations=5
    )
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="写首四行诗")]})

    assert out["iteration"] == 1
    assert out["final"] == "draft v1"


@pytest.mark.fast
def test_reflection_iterates_until_accept() -> None:
    """前两轮 critic 不满意,第三轮 ACCEPT。"""
    gen = FakeListChatModel(responses=["v1", "v2", "v3"])
    crit = FakeListChatModel(
        responses=["还要更精炼。", "再短一点。", "完美。ACCEPT"]
    )
    graph = build_reflection_graph(
        generator_llm=gen, critic_llm=crit, max_iterations=5
    )
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="x")]})

    assert out["iteration"] == 3
    assert out["final"] == "v3"


@pytest.mark.fast
def test_reflection_respects_max_iterations() -> None:
    """critic 永不 ACCEPT,达到 max_iterations 强制收尾。"""
    gen = FakeListChatModel(responses=["v1", "v2", "v3", "v4"])
    crit = FakeListChatModel(
        responses=["不行", "不行", "不行", "不行"]
    )
    graph = build_reflection_graph(
        generator_llm=gen, critic_llm=crit, max_iterations=2
    )
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="x")]})

    assert out["iteration"] == 2
    assert out["final"] == "v2"  # 最后一次 draft
```

- [ ] **Step 14.2：跑测试确认失败**

```bash
uv run pytest packages/agent_core/tests/patterns/test_reflection.py -v
```

Expected：ImportError。

- [ ] **Step 14.3：实现 reflection**

Create `packages/agent_core/src/agent_core/patterns/reflection.py`：

```python
"""Basic Reflection 模式 graph 工厂。

形态:
    START → generate → critic → (accept or max?)
                                 ├─ yes → finalize → END
                                 └─ no  → generate
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ..state import ReflectionState

_GEN_SYSTEM = (
    "你是写作助手。基于用户任务给出一份草稿。"
    "如果有上一轮 critique,请按 critique 调整。"
)
_CRIT_SYSTEM = (
    "你是 critic。指出草稿的问题与改进建议。"
    "若已经满意,在最后一行写 'ACCEPT'。"
)


def _extract_task(state: ReflectionState) -> str:
    """从 messages 末尾的 HumanMessage 抽 task。"""
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            return str(m.content)
    return ""


def build_reflection_graph(
    *,
    generator_llm: BaseChatModel,
    critic_llm: BaseChatModel,
    max_iterations: int = 3,
    accept_marker: str = "ACCEPT",
) -> CompiledStateGraph:
    """构造 Reflection graph。"""

    def generate_node(state: ReflectionState) -> dict[str, Any]:
        task = state.get("task") or _extract_task(state)
        prev_draft = state.get("draft", "")
        critique = state.get("critique", "")
        if prev_draft:
            user = (
                f"任务: {task}\n\n上一稿:\n{prev_draft}\n\n"
                f"critique:\n{critique}\n\n请基于 critique 改进,输出新稿。"
            )
        else:
            user = f"任务: {task}\n\n请输出第一稿。"
        out = generator_llm.invoke(
            [SystemMessage(content=_GEN_SYSTEM), HumanMessage(content=user)]
        )
        return {
            "task": task,
            "draft": str(out.content),
            "iteration": state.get("iteration", 0) + 1,
        }

    def critic_node(state: ReflectionState) -> dict[str, Any]:
        out = critic_llm.invoke(
            [
                SystemMessage(content=_CRIT_SYSTEM),
                HumanMessage(
                    content=f"任务:{state['task']}\n\n草稿:\n{state['draft']}"
                ),
            ]
        )
        return {"critique": str(out.content)}

    def finalize_node(state: ReflectionState) -> dict[str, Any]:
        return {"final": state["draft"]}

    def _decide(state: ReflectionState) -> str:
        critique = state.get("critique", "")
        if accept_marker in critique:
            return "finalize"
        if state.get("iteration", 0) >= max_iterations:
            return "finalize"
        return "generate"

    builder = StateGraph(ReflectionState)
    builder.add_node("generate", generate_node)
    builder.add_node("critic", critic_node)
    builder.add_node("finalize", finalize_node)
    builder.add_edge(START, "generate")
    builder.add_edge("generate", "critic")
    builder.add_conditional_edges(
        "critic", _decide, {"generate": "generate", "finalize": "finalize"}
    )
    builder.add_edge("finalize", END)
    return builder.compile()


__all__ = ["build_reflection_graph"]
```

- [ ] **Step 14.4：在 patterns `__init__.py` 加 re-export**

Replace `packages/agent_core/src/agent_core/patterns/__init__.py`：

```python
"""模式模板集合。"""

from __future__ import annotations

from .plan_execute import build_plan_execute_graph
from .react import build_react_graph
from .reflection import build_reflection_graph

__all__ = [
    "build_plan_execute_graph",
    "build_react_graph",
    "build_reflection_graph",
]
```

- [ ] **Step 14.5：跑测试确认通过**

```bash
uv run pytest packages/agent_core/tests/patterns/test_reflection.py -v
```

Expected：3 个测试全过。

- [ ] **Step 14.6：lint + type**

```bash
uv run ruff check packages/agent_core
uv run mypy packages/agent_core
```

Expected：均通过。

- [ ] **Step 14.7：提交**

```bash
git add packages/agent_core/src/agent_core/patterns/reflection.py packages/agent_core/src/agent_core/patterns/__init__.py packages/agent_core/tests/patterns/test_reflection.py
git commit -m "feat(agent-core): 添加 Reflection 模式 graph（generate → critic → 满意？）"
```

---

## Task 15：`agent_core.patterns.reflexion` —— Reflexion 模式 + ExperienceStore（TDD）

**Files:**
- Create: `packages/agent_core/tests/patterns/test_reflexion.py`
- Create: `packages/agent_core/src/agent_core/patterns/reflexion.py`
- Modify: `packages/agent_core/src/agent_core/patterns/__init__.py`
- Modify: `packages/agent_core/src/agent_core/__init__.py`（re-export ExperienceStore）

**设计要点：**
- Reflexion = Reflection + 经验记忆。失败案例的 critique 沉淀到 `experiences`，下一次尝试时作为 system prompt 一部分传入。
- `ExperienceStore` 是 `Protocol`，不依赖 M3 的 `packages/memory`。M2a 提供 `InMemoryExperienceStore`（dict 实现）。
- `build_reflexion_graph(*, actor_llm, critic_llm, store, max_iterations, success_marker="SUCCESS")`。
- 形态：START → recall（从 store 取相关经验放入 state.experiences）→ act → critic → 条件（SUCCESS or max？走 reflect : 回 act）→ reflect（把 critique 写入 store）→ act（再次循环）or END。

- [ ] **Step 15.1：写失败的测试**

Create `packages/agent_core/tests/patterns/test_reflexion.py`：

```python
"""Reflexion 模式 graph + ExperienceStore 测试。"""

from __future__ import annotations

import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.messages import HumanMessage

from agent_core import AgentRuntime
from agent_core.patterns.reflexion import (
    InMemoryExperienceStore,
    build_reflexion_graph,
)


@pytest.mark.fast
def test_reflexion_in_memory_store_roundtrip() -> None:
    """store.add → store.recall 应能取出。"""
    store = InMemoryExperienceStore()
    store.add(task="t1", experience="lesson A")
    store.add(task="t1", experience="lesson B")
    store.add(task="t2", experience="lesson C")

    assert set(store.recall("t1")) == {"lesson A", "lesson B"}
    assert store.recall("t2") == ["lesson C"]
    assert store.recall("nope") == []


@pytest.mark.fast
def test_reflexion_succeeds_on_first_attempt() -> None:
    """critic 第一轮就 SUCCESS,不需要积累经验。"""
    actor = FakeListChatModel(responses=["attempt 1"])
    crit = FakeListChatModel(responses=["完美。SUCCESS"])
    store = InMemoryExperienceStore()

    graph = build_reflexion_graph(
        actor_llm=actor,
        critic_llm=crit,
        store=store,
        max_iterations=5,
    )
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="任务 X")]})

    assert out["iteration"] == 1
    assert "attempt 1" in out["attempt"]


@pytest.mark.fast
def test_reflexion_accumulates_experiences_across_failures() -> None:
    """前两次失败,critique 进 store;第三次 SUCCESS。store 应有 2 条经验。"""
    actor = FakeListChatModel(responses=["a1", "a2", "a3"])
    crit = FakeListChatModel(
        responses=[
            "不对,缺论据。",
            "还是不行,引用源。",
            "OK。SUCCESS",
        ]
    )
    store = InMemoryExperienceStore()

    graph = build_reflexion_graph(
        actor_llm=actor,
        critic_llm=crit,
        store=store,
        max_iterations=5,
    )
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="任务 Y")]})

    assert out["iteration"] == 3
    # 失败的两条 critique 应写入 store
    recalled = store.recall("任务 Y")
    assert len(recalled) == 2


@pytest.mark.fast
def test_reflexion_recalls_existing_experiences_into_state() -> None:
    """store 已有该 task 的经验,recall 应把它们写入 state.experiences。"""
    store = InMemoryExperienceStore()
    store.add(task="任务 Z", experience="prior lesson 1")
    store.add(task="任务 Z", experience="prior lesson 2")

    actor = FakeListChatModel(responses=["x"])
    crit = FakeListChatModel(responses=["SUCCESS"])

    graph = build_reflexion_graph(
        actor_llm=actor, critic_llm=crit, store=store, max_iterations=3
    )
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="任务 Z")]})

    assert set(out["experiences"]) >= {"prior lesson 1", "prior lesson 2"}
```

- [ ] **Step 15.2：跑测试确认失败**

```bash
uv run pytest packages/agent_core/tests/patterns/test_reflexion.py -v
```

Expected：ImportError。

- [ ] **Step 15.3：实现 reflexion**

Create `packages/agent_core/src/agent_core/patterns/reflexion.py`：

```python
"""Reflexion 模式 graph 工厂 + ExperienceStore protocol。

经验记忆形态:
- ExperienceStore.recall(task) -> list[str] 取相关经验。
- ExperienceStore.add(task, experience) 把失败教训沉淀。

M2a 提供 InMemoryExperienceStore(dict 实现);
M3 packages/memory.episodic 会提供数据库后端实现,API 兼容。
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Protocol, runtime_checkable

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ..state import ReflexionState

_ACTOR_SYSTEM = (
    "你是任务执行者。如果给出了过往经验教训,请优先采纳避免重蹈覆辙。"
)
_CRITIC_SYSTEM = (
    "你是评估官。判断 attempt 是否解决了 task。"
    "若解决,在最后一行写 'SUCCESS';否则给出具体改进点。"
)


@runtime_checkable
class ExperienceStore(Protocol):
    """经验存储抽象。M2a 用 in-memory 实现;M3 接 packages/memory。"""

    def add(self, *, task: str, experience: str) -> None: ...
    def recall(self, task: str) -> list[str]: ...


class InMemoryExperienceStore:
    """简单 dict-backed 实现。线程不安全。"""

    def __init__(self) -> None:
        self._data: dict[str, list[str]] = defaultdict(list)

    def add(self, *, task: str, experience: str) -> None:
        if experience and experience not in self._data[task]:
            self._data[task].append(experience)

    def recall(self, task: str) -> list[str]:
        return list(self._data.get(task, []))


def _extract_task(state: ReflexionState) -> str:
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            return str(m.content)
    return ""


def build_reflexion_graph(
    *,
    actor_llm: BaseChatModel,
    critic_llm: BaseChatModel,
    store: ExperienceStore,
    max_iterations: int = 3,
    success_marker: str = "SUCCESS",
) -> CompiledStateGraph:
    """构造 Reflexion graph。"""

    def recall_node(state: ReflexionState) -> dict[str, Any]:
        task = state.get("task") or _extract_task(state)
        return {
            "task": task,
            "experiences": store.recall(task),
            "iteration": 0,
        }

    def act_node(state: ReflexionState) -> dict[str, Any]:
        exp = "\n".join(f"- {e}" for e in state.get("experiences", [])) or "(无)"
        prompt = (
            f"任务: {state['task']}\n\n过往经验教训:\n{exp}\n\n"
            "请给出一次 attempt。"
        )
        out = actor_llm.invoke(
            [SystemMessage(content=_ACTOR_SYSTEM), HumanMessage(content=prompt)]
        )
        return {
            "attempt": str(out.content),
            "iteration": state.get("iteration", 0) + 1,
        }

    def critic_node(state: ReflexionState) -> dict[str, Any]:
        out = critic_llm.invoke(
            [
                SystemMessage(content=_CRITIC_SYSTEM),
                HumanMessage(
                    content=(
                        f"任务: {state['task']}\n\n本轮 attempt:\n{state['attempt']}"
                    )
                ),
            ]
        )
        return {"critique": str(out.content)}

    def reflect_node(state: ReflexionState) -> dict[str, Any]:
        # 失败时把 critique 当作经验存入 store(成功时不存)
        critique = state.get("critique", "")
        if success_marker not in critique:
            store.add(task=state["task"], experience=critique)
            return {"experiences": [critique]}
        return {}

    def _decide(state: ReflexionState) -> str:
        critique = state.get("critique", "")
        if success_marker in critique:
            return END
        if state.get("iteration", 0) >= max_iterations:
            return END
        return "act"

    builder = StateGraph(ReflexionState)
    builder.add_node("recall", recall_node)
    builder.add_node("act", act_node)
    builder.add_node("critic", critic_node)
    builder.add_node("reflect", reflect_node)
    builder.add_edge(START, "recall")
    builder.add_edge("recall", "act")
    builder.add_edge("act", "critic")
    builder.add_edge("critic", "reflect")
    builder.add_conditional_edges(
        "reflect", _decide, {"act": "act", END: END}
    )
    return builder.compile()


__all__ = [
    "ExperienceStore",
    "InMemoryExperienceStore",
    "build_reflexion_graph",
]
```

- [ ] **Step 15.4：在 patterns / agent_core `__init__.py` 加 re-export**

Replace `packages/agent_core/src/agent_core/patterns/__init__.py`：

```python
"""模式模板集合。"""

from __future__ import annotations

from .plan_execute import build_plan_execute_graph
from .react import build_react_graph
from .reflection import build_reflection_graph
from .reflexion import (
    ExperienceStore,
    InMemoryExperienceStore,
    build_reflexion_graph,
)

__all__ = [
    "ExperienceStore",
    "InMemoryExperienceStore",
    "build_plan_execute_graph",
    "build_react_graph",
    "build_reflection_graph",
    "build_reflexion_graph",
]
```

Modify `packages/agent_core/src/agent_core/__init__.py`，在 `__all__` 与 import 块加上 4 个 build_*_graph 与 ExperienceStore / InMemoryExperienceStore：

```python
"""agent_core: Agent 抽象与运行时。

公开 API 一览:
- 状态: BaseAgentState / ReActState / PlanExecuteState / ReflectionState / ReflexionState
- 事件: AgentEvent / EventType / make_event
- 运行时: AgentRuntime / get_checkpointer / request_interrupt
- 模式: build_react_graph / build_plan_execute_graph / build_reflection_graph / build_reflexion_graph
- 记忆: ExperienceStore / InMemoryExperienceStore
"""

from __future__ import annotations

from .checkpointer import get_checkpointer
from .events import AgentEvent, EventType, make_event
from .interrupt import request_interrupt
from .patterns import (
    ExperienceStore,
    InMemoryExperienceStore,
    build_plan_execute_graph,
    build_react_graph,
    build_reflection_graph,
    build_reflexion_graph,
)
from .runtime import AgentRuntime
from .state import (
    BaseAgentState,
    PlanExecuteState,
    ReActState,
    ReflectionState,
    ReflexionState,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "AgentEvent",
    "AgentRuntime",
    "BaseAgentState",
    "EventType",
    "ExperienceStore",
    "InMemoryExperienceStore",
    "PlanExecuteState",
    "ReActState",
    "ReflectionState",
    "ReflexionState",
    "build_plan_execute_graph",
    "build_react_graph",
    "build_reflection_graph",
    "build_reflexion_graph",
    "get_checkpointer",
    "make_event",
    "request_interrupt",
]
```

- [ ] **Step 15.5：跑测试确认通过**

```bash
uv run pytest packages/agent_core/tests/patterns/test_reflexion.py -v
```

Expected：4 个测试全过。

- [ ] **Step 15.6：lint + type**

```bash
uv run ruff check packages/agent_core
uv run mypy packages/agent_core
```

Expected：均通过。

- [ ] **Step 15.7：提交**

```bash
git add packages/agent_core/src/agent_core/patterns/reflexion.py packages/agent_core/src/agent_core/patterns/__init__.py packages/agent_core/src/agent_core/__init__.py packages/agent_core/tests/patterns/test_reflexion.py
git commit -m "feat(agent-core): 添加 Reflexion 模式 graph + InMemoryExperienceStore"
```

---

## Task 16：M2a 验收 demo + 覆盖率 gate + 收尾

**Files:**
- Create: `examples/m2a_react_demo.py`
- Create: `tests/test_m2a_acceptance.py`
- Modify: `Makefile`（`coverage` 目标 `--cov=` 参数追加 tools / agent_core）
- Modify: `README.md`（路线图标记 M2a 进展，但不标 ✅；M2 完整结束后才打 v0.1.0）

- [ ] **Step 16.1：写 ReAct 验收 demo**

Create `examples/m2a_react_demo.py`：

```python
"""M2a 验收 demo:用 fake LLM 跑通 ReAct 完整循环。

运行方式:
    uv run python examples/m2a_react_demo.py

输出包含:tool 被调 → 拿结果 → AI 给最终答 三类信息。
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from agent_core import AgentRuntime, build_react_graph
from common.logging import configure_logging, get_logger
from tools import tool


class _ScriptedLLM(BaseChatModel):
    """Demo 用脚本化 LLM:第一轮发 tool_call,第二轮发最终答。"""

    responses: list[Any] = []
    idx: int = 0

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools: list[Any]) -> Any:  # noqa: ARG002
        return self

    def _generate(  # type: ignore[override]
        self,
        messages: list[Any],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        msg = self.responses[self.idx]
        self.idx += 1
        return ChatResult(generations=[ChatGeneration(message=msg)])


def main() -> int:
    configure_logging(level="INFO")
    log = get_logger("m2a.demo")

    @tool(name="add", description="把两个整数相加。")
    def add(a: int, b: int) -> int:
        return a + b

    llm = _ScriptedLLM(
        responses=[
            AIMessage(
                content="",
                tool_calls=[{"name": "add", "args": {"a": 7, "b": 5}, "id": "c1"}],
            ),
            AIMessage(content="7 + 5 = 12。"),
        ]
    )

    graph = build_react_graph(llm=llm, tools=[add])
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="算 7+5")]})

    log.info(
        "demo_done",
        message_count=len(out["messages"]),
        final=str(out["messages"][-1].content),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 16.2：写跨包验收 smoke 测试**

Create `tests/test_m2a_acceptance.py`：

```python
"""M2a 里程碑验收 smoke test。

验证 spec §9.M2 验收点:
1. tools 注册表 + 一个 builtin tool 可调
2. 4 种 pattern graph 都能用 fake LLM 跑通至少一道用例
3. AgentRuntime 能产出 AgentEvent 流
4. checkpointer 工厂在 dev 环境返回 MemorySaver
"""

from __future__ import annotations

from typing import Any

import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from agent_core import (
    AgentRuntime,
    EventType,
    InMemoryExperienceStore,
    build_plan_execute_graph,
    build_react_graph,
    build_reflection_graph,
    build_reflexion_graph,
    get_checkpointer,
)
from tools import get_tool, list_tools, tool


class _ScriptedLLM(BaseChatModel):
    responses: list[Any] = []
    idx: int = 0

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools: list[Any]) -> Any:  # noqa: ARG002
        return self

    def _generate(  # type: ignore[override]
        self,
        messages: list[Any],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        msg = self.responses[self.idx]
        self.idx += 1
        return ChatResult(generations=[ChatGeneration(message=msg)])


@pytest.fixture(autouse=True)
def _clear_registry() -> Any:
    from tools import registry as _reg

    _reg._REGISTRY.clear()
    yield
    _reg._REGISTRY.clear()


@pytest.mark.fast
def test_tool_registry_roundtrip() -> None:
    @tool(name="double", description="x")
    def double(x: int) -> int:
        return x * 2

    assert get_tool("double") is double
    assert any(t.name == "double" for t in list_tools())
    assert double.run({"x": 5}) == 10


@pytest.mark.fast
def test_react_pattern_smoke() -> None:
    @tool(name="add", description="加法")
    def add(a: int, b: int) -> int:
        return a + b

    llm = _ScriptedLLM(
        responses=[
            AIMessage(
                content="",
                tool_calls=[{"name": "add", "args": {"a": 1, "b": 2}, "id": "c1"}],
            ),
            AIMessage(content="3"),
        ]
    )
    runtime = AgentRuntime(build_react_graph(llm=llm, tools=[add]))
    out = runtime.invoke({"messages": [HumanMessage(content="1+2?")]})
    assert "3" in str(out["messages"][-1].content)


@pytest.mark.fast
def test_plan_execute_pattern_smoke() -> None:
    planner = FakeListChatModel(responses=["1. 一\n2. 二"])
    executor = FakeListChatModel(responses=["r1", "r2"])
    finalizer = FakeListChatModel(responses=["done"])
    runtime = AgentRuntime(
        build_plan_execute_graph(
            planner_llm=planner, executor_llm=executor, finalizer_llm=finalizer
        )
    )
    out = runtime.invoke({"messages": [HumanMessage(content="task")]})
    assert out["plan"] == ["一", "二"]
    assert out["final_answer"] == "done"


@pytest.mark.fast
def test_reflection_pattern_smoke() -> None:
    gen = FakeListChatModel(responses=["v1"])
    crit = FakeListChatModel(responses=["good. ACCEPT"])
    runtime = AgentRuntime(
        build_reflection_graph(generator_llm=gen, critic_llm=crit, max_iterations=3)
    )
    out = runtime.invoke({"messages": [HumanMessage(content="任务")]})
    assert out["final"] == "v1"


@pytest.mark.fast
def test_reflexion_pattern_smoke() -> None:
    actor = FakeListChatModel(responses=["a1"])
    crit = FakeListChatModel(responses=["SUCCESS"])
    store = InMemoryExperienceStore()
    runtime = AgentRuntime(
        build_reflexion_graph(
            actor_llm=actor, critic_llm=crit, store=store, max_iterations=3
        )
    )
    out = runtime.invoke({"messages": [HumanMessage(content="任务")]})
    assert "a1" in out["attempt"]


@pytest.mark.fast
async def test_runtime_astream_yields_events() -> None:
    llm = FakeListChatModel(responses=["hi back"])
    runtime = AgentRuntime(build_react_graph(llm=llm, tools=[]))
    events = [
        e
        async for e in runtime.astream(
            {"messages": [HumanMessage(content="hi")]}
        )
    ]
    types = {e.type for e in events}
    assert EventType.DONE in types


@pytest.mark.fast
def test_checkpointer_dev_factory() -> None:
    from langgraph.checkpoint.memory import MemorySaver

    cp = get_checkpointer(env="dev")
    assert isinstance(cp, MemorySaver)


@pytest.mark.fast
def test_m2a_demo_script_main_callable() -> None:
    """examples/m2a_react_demo.py 必须可被 import 且 main 可调。"""
    import importlib.util
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    demo = repo_root / "examples" / "m2a_react_demo.py"
    assert demo.exists()
    spec = importlib.util.spec_from_file_location("m2a_demo", demo)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)
```

- [ ] **Step 16.3：跑全量覆盖率验证**

```bash
uv run pytest packages/common packages/llm_providers packages/tools packages/agent_core tests \
  --cov=common --cov=llm_providers --cov=tools --cov=agent_core \
  --cov-report=term-missing --cov-fail-under=80
```

Expected：覆盖率 ≥ 80%。如未达,读 term-missing 报告补测试再回来。

- [ ] **Step 16.4：跑 demo import smoke**

```bash
uv run python -c "import importlib.util; spec = importlib.util.spec_from_file_location('m2a_demo', 'examples/m2a_react_demo.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('demo importable, main =', m.main)"
```

Expected：`demo importable, main = <function main at 0x...>`,无 ImportError。

- [ ] **Step 16.5：在 Makefile 把新包加入 coverage 目标**

Modify `Makefile`，把 `coverage:` 行改为：

```makefile
coverage:
	uv run pytest packages tests --cov=common --cov=llm_providers --cov=tools --cov=agent_core --cov-report=term-missing --cov-fail-under=80
```

- [ ] **Step 16.6：跑 make 全套**

```bash
make lint
make type
make test
make coverage
```

Expected：全部通过。

- [ ] **Step 16.7：在根 README 路线图标记 M2 进度**

修改 `README.md` 路线图,把 M2 那一行改为：

```
| **M2** | lessons 1–6 + `tools` + `agent_core`（M2a SDK 已交付） | `v0.1.0`(待 M2b) |
```

> 不打 ✅,因为 M2 完整结束需要 M2b（lessons）也交付。

- [ ] **Step 16.8：提交收尾**

```bash
git add examples/m2a_react_demo.py tests/test_m2a_acceptance.py Makefile README.md
git commit -m "chore(m2a): 添加验收 demo + 跨包 smoke 测试 + 覆盖率 gate 扩展到 4 个包"
```

- [ ] **Step 16.9：fast-forward 合回 main 并删 feature 分支**

```bash
git checkout main
git merge feat/m2a-tools-and-agent-core --ff-only
git branch -d feat/m2a-tools-and-agent-core
```

Expected：fast-forward 成功;feature 分支删除成功。

- [ ] **Step 16.10：（可选）打中间 tag**

```bash
git tag -a m2a-complete -m "M2a packages/tools + packages/agent_core 完成（4 patterns + 5 builtin tools）"
```

不打 `v0.1.0` —— 该 tag 留到 M2b（lessons 1-6）完成。

- [ ] **Step 16.11：查看完整 commit 链**

```bash
git log --oneline | head -25
```

Expected：约 16-18 条 M2a commit + 之前的 M0/M1 历史。

---

## Self-Review

### Spec 覆盖检查（spec §4.2 + §9.M2）

| Spec 要求 | 对应 Task | 状态 |
|---|---|---|
| `tools/base.py` (Tool 抽象基类) | Task 2 | ✓ |
| `tools/registry.py` (`@tool` 装饰器自动注册) | Task 3 | ✓ |
| `tools/builtin/web_search.py` (Tavily) | Task 4 | ✓ |
| `tools/builtin/web_scrape.py` (trafilatura + readability) | Task 4 | ✓ |
| `tools/builtin/python_repl.py` (M2a 安全简版,真沙箱留 M4) | Task 5 | ✓ |
| `tools/builtin/file_io.py` (路径白名单) | Task 5 | ✓ |
| `tools/builtin/shell.py` (命令白名单) | Task 5 | ✓ |
| `tools/builtin/vector_search.py` (依赖 retrieval) | — | 推迟到 M3(retrieval 出来后) |
| `tools/builtin/sql_query.py` (依赖 db schema) | — | 推迟到 M3 |
| `tools/mcp_adapter.py` | — | 推迟到 M4 第 15 章 |
| `agent_core/state.py` (BaseAgentState + 各 pattern state) | Task 8 | ✓ |
| `agent_core/runtime.py` (AgentRuntime invoke/astream) | Task 11 | ✓ |
| `agent_core/events.py` (16 种事件类型) | Task 7 | ✓ |
| `agent_core/checkpointer.py` (dev MemorySaver, prod Postgres 留 M3) | Task 9 | ✓ |
| `agent_core/interrupt.py` (HITL 包装) | Task 10 | ✓ |
| `agent_core/patterns/react.py` | Task 12 | ✓ |
| `agent_core/patterns/plan_execute.py` | Task 13 | ✓ |
| `agent_core/patterns/reflection.py` | Task 14 | ✓ |
| `agent_core/patterns/reflexion.py` (含 ExperienceStore) | Task 15 | ✓ |
| `agent_core/patterns/supervisor / hierarchical / swarm / network` | — | 全部 M3(spec §9.M3 列出) |
| 80% 覆盖率 | Task 16 | ✓ |
| 验收: ReAct pattern 跑通至少一道用例 | Task 12 + Task 16 | ✓ |
| 验收: 每个 pattern 都有 fake-LLM 测试 | Task 12-15 | ✓ |

### 占位符扫描

已检查全文,无 "TBD" / "TODO" / "fill in" / "实现细节略"。

特殊点说明:
- Task 11 步骤 11.3 / 11.4 的"Note for implementer"说明 LangGraph compile 后无法注入 checkpointer 的限制,Step 11.4 给出了简化后的 `__init__` 与对应测试调整代码——这不是占位符,是显式的"按这个版本实现"指令。

### 类型 / 接口一致性

- `Tool` —— Task 2 定义,Task 3/4/5 引用,Task 12 通过 `tools` 列表传给 `bind_tools`。
- `tool` 装饰器 / `get_tool` / `list_tools` —— Task 3 定义,Task 4/5/12-15 测试引用。
- `ToolError` —— common.errors.ToolError,Task 2/4/5 引用。
- `ConfigError` —— common.errors.ConfigError,Task 3/4 引用(重名 / 未注册 / 缺 key)。
- `AgentEvent` / `EventType` / `make_event` —— Task 7 定义,Task 11/16 引用,Self-Review 验收覆盖。
- `BaseAgentState` / `ReActState` / `PlanExecuteState` / `ReflectionState` / `ReflexionState` —— Task 8 定义,Task 11/12-15 引用。
- `AgentRuntime(graph, *, checkpointer, cost_tracker)` —— Task 11 定义,Task 12-16 测试引用。invoke / astream 签名一致。
- `get_checkpointer(*, env)` —— Task 9 定义,Task 11 测试引用,Task 16 smoke 引用。
- `request_interrupt(*, reason, payload)` —— Task 10 定义,M4 第 12 章 lessons 会消费。
- `build_react_graph(*, llm, tools, system_prompt)` —— Task 12 定义,Task 16 smoke 引用。
- `build_plan_execute_graph(*, planner_llm, executor_llm, finalizer_llm, max_steps)` —— Task 13 定义,Task 16 smoke 引用。
- `build_reflection_graph(*, generator_llm, critic_llm, max_iterations, accept_marker)` —— Task 14 定义,Task 16 smoke 引用。
- `build_reflexion_graph(*, actor_llm, critic_llm, store, max_iterations, success_marker)` —— Task 15 定义,Task 16 smoke 引用。
- `ExperienceStore` Protocol + `InMemoryExperienceStore` —— Task 15 定义。M3 packages/memory.episodic 应该提供数据库后端实现(参数 / 返回类型必须保持一致)。

### Scope 检查

本计划严格限定于 M2a 子里程碑(packages/tools + packages/agent_core 的核心子集)。**不引入：**
- lessons 1-6 内容（属 M2b）
- packages/memory（属 M3）
- packages/retrieval（属 M3）
- agent_core/patterns/{supervisor, hierarchical, swarm, network}（属 M3）
- vector_search / sql_query / mcp_adapter 工具（属 M3 / M4）
- agent_core/checkpointer 的 PostgresSaver（属 M3）
- 完整 AgentRuntime 事件映射（plan.* / subtask.* / cost.update 等，属 M4 第 12 章）
- packages/{tracing, evaluation, guardrails, sandbox}（属 M4）
- capstone（属 M5）

### 已知 deferred work（不属于 M2a，但需在 M2b/M3 处理）

1. **`tools.builtin.vector_search` / `sql_query`**：M3 retrieval 包出来后补。
2. **`tools.builtin.mcp_adapter`**：M4 第 15 章。
3. **`agent_core.checkpointer` Postgres 后端**：M3。
4. **`agent_core.runtime` 完整事件映射**：M4 第 12 章。
5. **`agent_core/patterns/supervisor / hierarchical / swarm / network`**：M3 lessons 10-11。
6. **`packages/memory.episodic` 替换 InMemoryExperienceStore**：M3 lessons 7。
7. **lessons 1-6 全套教学内容**：M2b。

---

**计划完成。共 16 个 Task,预估 16-20 次 commit + 若干修复 commit,完整执行时间约 5-8 小时。**

按 plan 完成后下一步:M2b（lessons 1-6 + 打 v0.1.0 tag）。
