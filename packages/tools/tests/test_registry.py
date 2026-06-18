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
