"""手写 plan-execute agent：规划 → 逐步执行 → 汇总。

类比前端:
    - Planner ≈ 项目经理（拆任务）
    - Executor ≈ 开发者（逐个完成）
    - Finalizer ≈ QA review（汇总出终版）
    - Plan DAG ≈ 依赖图（Task A → Task B → Task C）

核心思路:
    1. planner 把大任务拆成小步骤（编号列表）
    2. executor 逐个执行每一步
    3. finalizer 汇总所有结果出终版

对比 agent_core.build_plan_execute_graph:
    手写版看清底层，prebuilt 版封装标准模式。
"""

from __future__ import annotations

import re

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage


def _parse_plan(plan_text: str) -> list[str]:
    """从编号列表文本中解析出步骤列表。

    支持格式:
        1. 步骤一
        2. 步骤二
    或:
        1、步骤一
        2、步骤二
    """
    pattern = r"^\s*\d+[.、]\s*(.+)$"
    matches = re.findall(pattern, plan_text, flags=re.MULTILINE)
    return [m.strip() for m in matches if m.strip()]


def run_plan_execute(
    planner_llm: BaseChatModel,
    executor_llm: BaseChatModel,
    finalizer_llm: BaseChatModel,
    user_input: str,
) -> dict[str, str | list[str]]:
    """手写 plan-execute agent（不依赖 LangGraph，看清底层）。

    Args:
        planner_llm: 规划器 LLM。
        executor_llm: 执行器 LLM。
        finalizer_llm: 汇总器 LLM。
        user_input: 用户输入。

    Returns:
        包含 plan / step_results / final_answer 的 dict。
    """
    # Step 1: planner 拆任务
    plan_response = planner_llm.invoke([HumanMessage(content=user_input)])
    plan = _parse_plan(str(plan_response.content))

    # Step 2: executor 逐个执行
    step_results: list[str] = []
    for step in plan:
        exec_response = executor_llm.invoke([HumanMessage(content=step)])
        step_results.append(str(exec_response.content))

    # Step 3: finalizer 汇总
    summary_prompt = (
        f"任务: {user_input}\n计划: {plan}\n执行结果: {step_results}\n请汇总出最终答案。"
    )
    final_response = finalizer_llm.invoke([HumanMessage(content=summary_prompt)])

    return {
        "plan": plan,
        "step_results": step_results,
        "final_answer": str(final_response.content),
    }
