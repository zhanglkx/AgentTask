"""Agent 运行时。

把 LangGraph CompiledStateGraph 包成统一接口:
- invoke: 同步,返回终态(含 error 兜底)。
- astream: 异步,产出 AgentEvent 流(M2a 简版,M4 扩展)。
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver

from common.cost import CostTracker

from .events import AgentEvent, EventType, make_event


class AgentRuntime:
    """统一 agent 运行入口。

    Args:
        graph: 已 compile 的 StateGraph(checkpointer 在 compile 时传入)。
        checkpointer: 可选,用于 thread_id 续传。
        cost_tracker: 可选,M2a 暂未消费,留接口给 M4 cost 事件。
    """

    def __init__(
        self,
        graph: Any,
        *,
        checkpointer: BaseCheckpointSaver[Any] | None = None,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        self._graph = graph
        self._checkpointer = checkpointer
        self._cost_tracker = cost_tracker

    def _config_for(self, thread_id: str) -> RunnableConfig:
        cfg: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        return cfg

    def invoke(
        self,
        graph_input: dict[str, Any],
        *,
        thread_id: str = "default",
    ) -> dict[str, Any]:
        """同步执行 graph,异常被捕获并写入 state.error。"""
        try:
            return dict(self._graph.invoke(graph_input, config=self._config_for(thread_id)))
        except Exception as e:
            return {
                **graph_input,
                "error": f"{type(e).__name__}: {e}",
            }

    async def astream(
        self,
        graph_input: dict[str, Any],
        *,
        thread_id: str = "default",
    ) -> AsyncIterator[AgentEvent]:
        """异步执行,产出标准化事件流。

        M2a 简版:
        - 每个 node 执行完后 emit 一条 message.delta(若产生新 AIMessage)。
        - 全部完成 emit 一条 done。
        - 异常 emit 一条 error + 一条 done。
        """
        try:
            async for chunk in self._graph.astream(
                graph_input, config=self._config_for(thread_id), stream_mode="updates"
            ):
                for node_name, partial_state in chunk.items():
                    msgs = (
                        partial_state.get("messages") if isinstance(partial_state, dict) else None
                    )
                    if msgs:
                        for m in msgs:
                            if isinstance(m, AIMessage):
                                yield make_event(
                                    type=EventType.MESSAGE_DELTA,
                                    payload={"content": str(m.content)},
                                    node=node_name,
                                )
        except Exception as e:
            yield make_event(
                type=EventType.ERROR,
                payload={"message": f"{type(e).__name__}: {e}"},
            )
        yield make_event(type=EventType.DONE)


__all__ = ["AgentRuntime"]
