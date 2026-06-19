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
    events = [e async for e in runtime.astream({"messages": [HumanMessage(content="hi")]})]
    assert any(e.type is EventType.DONE for e in events)


@pytest.mark.fast
async def test_runtime_astream_emits_error_then_done() -> None:
    """graph 抛错时 astream 应 emit 一条 error + 一条 done。"""
    runtime = AgentRuntime(_build_failing_graph())
    events = [e async for e in runtime.astream({"messages": [HumanMessage(content="x")]})]
    types = [e.type for e in events]
    assert EventType.ERROR in types
    assert EventType.DONE in types
    err_event = next(e for e in events if e.type is EventType.ERROR)
    assert "kaboom" in err_event.payload.get("message", "")


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
    runtime.invoke({"messages": [HumanMessage(content="a")]}, thread_id="t1")
    out2 = runtime.invoke({"messages": [HumanMessage(content="b")]}, thread_id="t1")
    assert len(out2["messages"]) >= 4
