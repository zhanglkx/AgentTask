"""tool_loop 测试：手写工具循环验证。"""

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from tool_loop import run_tool_loop


class _ScriptedLLM(BaseChatModel):
    responses: list[Any] = []  # noqa: RUF012
    idx: int = 0

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(  # type: ignore[override]
        self,
        tools: list[Any],
        **kwargs: Any,
    ) -> Any:
        return self

    def _generate(
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
def _clear_registry() -> None:
    from tools import registry as _reg

    _reg._REGISTRY.clear()


@pytest.mark.fast
def test_tool_loop_single_tool_call() -> None:
    """手写循环：一次 tool call + 一次最终回答。"""
    from tools import tool

    @tool(name="add", description="加法")
    def add(a: int, b: int) -> int:
        return a + b

    llm = _ScriptedLLM(
        responses=[
            AIMessage(
                content="",
                tool_calls=[{"name": "add", "args": {"a": 3, "b": 4}, "id": "c1"}],
            ),
            AIMessage(content="3 + 4 = 7"),
        ]
    )
    result = run_tool_loop(llm, "算 3+4", [add])
    assert "7" in str(result[-1].content)


@pytest.mark.fast
def test_tool_loop_no_tool_call() -> None:
    """无 tool call 时直接返回 AI 回答。"""
    llm = _ScriptedLLM(
        responses=[AIMessage(content="直接回答")],
    )
    result = run_tool_loop(llm, "hi", [])
    assert str(result[-1].content) == "直接回答"


@pytest.mark.fast
def test_tool_loop_multiple_tool_calls() -> None:
    """并行 tool calls：一次多个调用。"""
    from tools import tool

    @tool(name="mul", description="乘法")
    def mul(a: int, b: int) -> int:
        return a * b

    llm = _ScriptedLLM(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "mul", "args": {"a": 2, "b": 3}, "id": "c1"},
                    {"name": "mul", "args": {"a": 4, "b": 5}, "id": "c2"},
                ],
            ),
            AIMessage(content="2×3=6, 4×5=20"),
        ]
    )
    result = run_tool_loop(llm, "算", [mul])
    assert "6" in str(result[-1].content)
