"""Reflexion 模式 graph 工厂 + ExperienceStore protocol。

经验记忆形态:
- ExperienceStore.recall(task) -> list[str] 取相关经验。
- ExperienceStore.add(task, experience) 把失败教训沉淀。

M2a 提供 InMemoryExperienceStore(dict 实现);
M3 packages/memory.episodic 会提供数据库后端实现,API 兼容。
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Protocol, runtime_checkable

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from ..state import ReflexionState

_ACTOR_SYSTEM = "你是任务执行者。如果给出了过往经验教训,请优先采纳避免重蹈覆辙。"
_CRITIC_SYSTEM = (
    "你是评估官。判断 attempt 是否解决了 task。"
    "若解决,在最后一行写 'SUCCESS';否则给出具体改进点。"
)


@runtime_checkable
class ExperienceStore(Protocol):
    """经验存储抽象。M2a 用 in-memory 实现;M3 接 packages/memory。"""

    def add(self, *, task: str, experience: str) -> None: ...
    def recall(self, task: str) -> list[str]: ...


class InMemoryExperienceStore:
    """简单 dict-backed 实现。线程不安全。"""

    def __init__(self) -> None:
        self._data: dict[str, list[str]] = defaultdict(list)

    def add(self, *, task: str, experience: str) -> None:
        if experience and experience not in self._data[task]:
            self._data[task].append(experience)

    def recall(self, task: str) -> list[str]:
        return list(self._data.get(task, []))


def _extract_task(state: ReflexionState) -> str:
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            return str(m.content)
    return ""


def build_reflexion_graph(
    *,
    actor_llm: BaseChatModel,
    critic_llm: BaseChatModel,
    store: ExperienceStore,
    max_iterations: int = 3,
    success_marker: str = "SUCCESS",
) -> Any:
    """构造 Reflexion graph。"""

    def recall_node(state: ReflexionState) -> dict[str, Any]:
        task = state.get("task") or _extract_task(state)
        return {
            "task": task,
            "experiences": store.recall(task),
            "iteration": 0,
        }

    def act_node(state: ReflexionState) -> dict[str, Any]:
        exp = "\n".join(f"- {e}" for e in state.get("experiences", [])) or "(无)"
        prompt = f"任务: {state['task']}\n\n过往经验教训:\n{exp}\n\n" "请给出一次 attempt。"
        out = actor_llm.invoke([SystemMessage(content=_ACTOR_SYSTEM), HumanMessage(content=prompt)])
        return {
            "attempt": str(out.content),
            "iteration": state.get("iteration", 0) + 1,
        }

    def critic_node(state: ReflexionState) -> dict[str, Any]:
        out = critic_llm.invoke(
            [
                SystemMessage(content=_CRITIC_SYSTEM),
                HumanMessage(content=f"任务: {state['task']}\n\n本轮 attempt:\n{state['attempt']}"),
            ]
        )
        return {"critique": str(out.content)}

    def reflect_node(state: ReflexionState) -> dict[str, Any]:
        critique = state.get("critique", "")
        if success_marker not in critique:
            store.add(task=state["task"], experience=critique)
            return {"experiences": [critique]}
        return {}

    def _decide(state: ReflexionState) -> str:
        critique = state.get("critique", "")
        if success_marker in critique:
            return END
        if state.get("iteration", 0) >= max_iterations:
            return END
        return "act"

    builder = StateGraph(ReflexionState)
    builder.add_node("recall", recall_node)
    builder.add_node("act", act_node)
    builder.add_node("critic", critic_node)
    builder.add_node("reflect", reflect_node)
    builder.add_edge(START, "recall")
    builder.add_edge("recall", "act")
    builder.add_edge("act", "critic")
    builder.add_edge("critic", "reflect")
    builder.add_conditional_edges("reflect", _decide, {"act": "act", END: END})
    return builder.compile()


__all__ = [
    "ExperienceStore",
    "InMemoryExperienceStore",
    "build_reflexion_graph",
]
