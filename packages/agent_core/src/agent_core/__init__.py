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
    "__version__",
    "build_plan_execute_graph",
    "build_react_graph",
    "build_reflection_graph",
    "build_reflexion_graph",
    "get_checkpointer",
    "make_event",
    "request_interrupt",
]
