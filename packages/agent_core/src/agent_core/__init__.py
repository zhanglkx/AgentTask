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
    "AgentEvent",
    "AgentRuntime",
    "BaseAgentState",
    "EventType",
    "PlanExecuteState",
    "ReActState",
    "ReflectionState",
    "ReflexionState",
    "__version__",
    "get_checkpointer",
    "make_event",
    "request_interrupt",
]
