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

    def _run(self, a: int, b: int) -> int:  # type: ignore[override,unused-ignore]
        return a + b


class _Boom(Tool):
    name: str = "boom"
    description: str = "故意失败。"
    args_schema: type[BaseModel] = _AddInput

    def _run(self, a: int, b: int) -> int:  # type: ignore[override,unused-ignore]
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
