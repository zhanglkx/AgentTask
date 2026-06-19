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
    """构造一个 fake LLM:第一轮回 tool_call,第二轮回最终答。"""
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.outputs import ChatGeneration, ChatResult

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
    graph = build_react_graph(llm=llm, tools=[], system_prompt="你是研究助手。")
    runtime = AgentRuntime(graph)

    out = runtime.invoke({"messages": [HumanMessage(content="hi")]})
    assert any(
        isinstance(m, SystemMessage) and "研究助手" in str(m.content) for m in out["messages"]
    )
