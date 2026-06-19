"""Plan-Execute 模式 graph 测试。"""

from __future__ import annotations

from typing import Any

import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.messages import HumanMessage

from agent_core import AgentRuntime
from agent_core.patterns.plan_execute import build_plan_execute_graph


def _scripted_llm(responses: list[str]) -> Any:
    """FakeListChatModel 在每次 invoke 取下一个字符串作为 AI 响应。"""
    return FakeListChatModel(responses=responses)


@pytest.mark.fast
def test_plan_execute_runs_all_steps() -> None:
    """planner 出 3 步 → executor 各执行一次 → finalize 合成。"""
    planner_llm = _scripted_llm(responses=["1. 查找资料\n2. 整理要点\n3. 撰写答案"])
    executor_llm = _scripted_llm(responses=["资料: A B C", "要点: A>B", "草稿"])
    finalizer_llm = _scripted_llm(responses=["最终答: A 优于 B"])

    graph = build_plan_execute_graph(
        planner_llm=planner_llm,
        executor_llm=executor_llm,
        finalizer_llm=finalizer_llm,
    )
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="比较 A 和 B")]})

    assert out.get("plan")
    assert len(out["plan"]) == 3
    assert len(out["step_results"]) == 3
    assert "最终答" in out["final_answer"]


@pytest.mark.fast
def test_plan_execute_respects_max_steps() -> None:
    """planner 出 100 步,设置 max_steps=2 → 最多执行 2 步后强制 finalize。"""
    big_plan = "\n".join(f"{i}. step{i}" for i in range(1, 101))
    planner_llm = _scripted_llm(responses=[big_plan])
    executor_llm = _scripted_llm(responses=["r1", "r2", "r3"])
    finalizer_llm = _scripted_llm(responses=["truncated"])

    graph = build_plan_execute_graph(
        planner_llm=planner_llm,
        executor_llm=executor_llm,
        finalizer_llm=finalizer_llm,
        max_steps=2,
    )
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="x")]})

    assert len(out["step_results"]) == 2


@pytest.mark.fast
def test_plan_execute_empty_plan_goes_to_finalize() -> None:
    """planner 没出步骤 → 直接 finalize。"""
    planner_llm = _scripted_llm(responses=[""])
    executor_llm = _scripted_llm(responses=[])
    finalizer_llm = _scripted_llm(responses=["nothing to do"])

    graph = build_plan_execute_graph(
        planner_llm=planner_llm,
        executor_llm=executor_llm,
        finalizer_llm=finalizer_llm,
    )
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="trivial")]})

    assert out["plan"] == []
    assert out["step_results"] == []
    assert "nothing" in out["final_answer"]
