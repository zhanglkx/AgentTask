"""Plan-Execute 模式 graph 工厂。

形态:
    START → planner → executor → (still steps?) → executor → ... → finalize → END

planner: 把用户问题拆成 list[str] 步骤。
executor: 按 current_step 执行单步,把结果写入 step_results。
finalize: 用 plan + step_results 合成最终答。
"""

from __future__ import annotations

import re
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from ..state import PlanExecuteState

_PLANNER_SYSTEM = (
    "你是任务分解专家。把用户的问题拆成 3-7 个原子步骤,"
    "每步一行,以 '1. ' / '2. ' / ... 开头。如果问题不需要分步,直接输出空。"
)
_EXECUTOR_SYSTEM = (
    "你正在执行一个步骤。已知整体计划与已执行结果。只输出当前步骤的产出,不要重复整体计划。"
)
_FINALIZER_SYSTEM = "你是总结员。基于计划与每步结果,给出最终答复给用户。"


def _parse_plan(text: str) -> list[str]:
    """从 LLM 输出里抽出步骤行。空输入返回 []。"""
    if not text.strip():
        return []
    steps: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^\s*(\d+)[\.\)]\s*(.+)$", line)
        if m:
            steps.append(m.group(2).strip())
    return steps


def build_plan_execute_graph(
    *,
    planner_llm: BaseChatModel,
    executor_llm: BaseChatModel,
    finalizer_llm: BaseChatModel,
    max_steps: int = 10,
) -> Any:
    """构造 Plan-Execute graph(已 compile)。

    Args:
        planner_llm / executor_llm / finalizer_llm: 三个角色 LLM(可同一实例)。
        max_steps: 安全上限,防止 planner 出过多步骤把 token 烧光。
    """

    def planner_node(state: PlanExecuteState) -> dict[str, Any]:
        msgs = [SystemMessage(content=_PLANNER_SYSTEM), *state["messages"]]
        out = planner_llm.invoke(msgs)
        plan = _parse_plan(str(out.content))[:max_steps]
        return {"plan": plan, "current_step": 0, "step_results": []}

    def executor_node(state: PlanExecuteState) -> dict[str, Any]:
        idx = state.get("current_step", 0)
        plan = state.get("plan", [])
        if idx >= len(plan) or idx >= max_steps:
            return {"current_step": idx}
        step = plan[idx]
        already = state.get("step_results", [])
        context = "\n".join(f"步骤 {i + 1}: {plan[i]}\n结果: {r}" for i, r in enumerate(already))
        prompt = (
            "整体计划:\n"
            + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(plan))
            + f"\n\n已执行:\n{context}\n\n现在执行第 {idx + 1} 步: {step}"
        )
        out = executor_llm.invoke(
            [SystemMessage(content=_EXECUTOR_SYSTEM), HumanMessage(content=prompt)]
        )
        return {
            "step_results": [str(out.content)],
            "current_step": idx + 1,
        }

    def finalizer_node(state: PlanExecuteState) -> dict[str, Any]:
        plan = state.get("plan", [])
        results = state.get("step_results", [])
        body = (
            "\n".join(
                f"步骤 {i + 1}: {plan[i] if i < len(plan) else ''}\n结果: {r}"
                for i, r in enumerate(results)
            )
            or "(无步骤)"
        )
        prompt = f"原始问题对话见上文。计划与结果:\n{body}\n\n请给出最终答复。"
        msgs = [
            SystemMessage(content=_FINALIZER_SYSTEM),
            *state["messages"],
            HumanMessage(content=prompt),
        ]
        out = finalizer_llm.invoke(msgs)
        return {"final_answer": str(out.content)}

    def _should_continue(state: PlanExecuteState) -> str:
        idx = state.get("current_step", 0)
        plan = state.get("plan", [])
        if idx < len(plan) and idx < max_steps:
            return "executor"
        return "finalizer"

    builder = StateGraph(PlanExecuteState)
    builder.add_node("planner", planner_node)
    builder.add_node("executor", executor_node)
    builder.add_node("finalizer", finalizer_node)
    builder.add_edge(START, "planner")
    builder.add_conditional_edges(
        "planner",
        _should_continue,
        {"executor": "executor", "finalizer": "finalizer"},
    )
    builder.add_conditional_edges(
        "executor",
        _should_continue,
        {"executor": "executor", "finalizer": "finalizer"},
    )
    builder.add_edge("finalizer", END)
    return builder.compile()


__all__ = ["build_plan_execute_graph"]
