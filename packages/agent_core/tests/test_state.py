"""state 定义测试。"""

from __future__ import annotations

from typing import Any, get_type_hints

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
    assert len(list(merged)) == 2
