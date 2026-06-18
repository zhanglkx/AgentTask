"""AgentEvent 行为测试。"""

from __future__ import annotations

from datetime import UTC, datetime

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
    assert e.timestamp.tzinfo == UTC
    assert e.type == "message.delta"
    assert e.payload == {"content": "hi"}
    assert e.node == "agent"
    assert e.trace_id is None


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
            timestamp=datetime.now(tz=UTC),
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
