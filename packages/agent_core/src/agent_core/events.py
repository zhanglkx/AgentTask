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
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class EventType(enum.StrEnum):
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
    type: str | EventType,  # noqa: A002 - 对外契约字段名,与 SSE event 字段一致
    payload: dict[str, Any] | None = None,
    node: str | None = None,
    trace_id: str | None = None,
) -> AgentEvent:
    """构造一个 AgentEvent,自动填 id 与时间戳。"""
    return AgentEvent(
        event_id=uuid.uuid4().hex,
        type=EventType(type) if not isinstance(type, EventType) else type,
        timestamp=datetime.now(tz=UTC),
        payload=payload or {},
        node=node,
        trace_id=trace_id,
    )


__all__ = ["AgentEvent", "EventType", "make_event"]
