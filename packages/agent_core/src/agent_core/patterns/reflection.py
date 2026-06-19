"""Basic Reflection 模式 graph 工厂。

形态:
    START → generate → critic → (accept or max?)
                                 ├─ yes → finalize → END
                                 └─ no  → generate
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from ..state import ReflectionState

_GEN_SYSTEM = (
    "你是写作助手。基于用户任务给出一份草稿。" "如果有上一轮 critique,请按 critique 调整。"
)
_CRIT_SYSTEM = "你是 critic。指出草稿的问题与改进建议。" "若已经满意,在最后一行写 'ACCEPT'。"


def _extract_task(state: ReflectionState) -> str:
    """从 messages 末尾的 HumanMessage 抽 task。"""
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            return str(m.content)
    return ""


def build_reflection_graph(
    *,
    generator_llm: BaseChatModel,
    critic_llm: BaseChatModel,
    max_iterations: int = 3,
    accept_marker: str = "ACCEPT",
) -> Any:
    """构造 Reflection graph。"""

    def generate_node(state: ReflectionState) -> dict[str, Any]:
        task = state.get("task") or _extract_task(state)
        prev_draft = state.get("draft", "")
        critique = state.get("critique", "")
        if prev_draft:
            user = (
                f"任务: {task}\n\n上一稿:\n{prev_draft}\n\n"
                f"critique:\n{critique}\n\n请基于 critique 改进,输出新稿。"
            )
        else:
            user = f"任务: {task}\n\n请输出第一稿。"
        out = generator_llm.invoke([SystemMessage(content=_GEN_SYSTEM), HumanMessage(content=user)])
        return {
            "task": task,
            "draft": str(out.content),
            "iteration": state.get("iteration", 0) + 1,
        }

    def critic_node(state: ReflectionState) -> dict[str, Any]:
        out = critic_llm.invoke(
            [
                SystemMessage(content=_CRIT_SYSTEM),
                HumanMessage(content=f"任务:{state['task']}\n\n草稿:\n{state['draft']}"),
            ]
        )
        return {"critique": str(out.content)}

    def finalize_node(state: ReflectionState) -> dict[str, Any]:
        return {"final": state["draft"]}

    def _decide(state: ReflectionState) -> str:
        critique = state.get("critique", "")
        if accept_marker in critique:
            return "finalize"
        if state.get("iteration", 0) >= max_iterations:
            return "finalize"
        return "generate"

    builder = StateGraph(ReflectionState)
    builder.add_node("generate", generate_node)
    builder.add_node("critic", critic_node)
    builder.add_node("finalize", finalize_node)
    builder.add_edge(START, "generate")
    builder.add_edge("generate", "critic")
    builder.add_conditional_edges(
        "critic", _decide, {"generate": "generate", "finalize": "finalize"}
    )
    builder.add_edge("finalize", END)
    return builder.compile()


__all__ = ["build_reflection_graph"]
