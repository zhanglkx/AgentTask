"""plan_execute_agent 测试：手写 plan-execute agent 验证。"""

from __future__ import annotations

import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.messages import HumanMessage

from plan_execute_agent import run_plan_execute


@pytest.mark.fast
def test_plan_execute_basic() -> None:
    """基本 plan-execute：规划 → 逐步执行 → 汇总。"""
    planner = FakeListChatModel(responses=["1. 调查背景\n2. 分析数据\n3. 写总结"])
    executor = FakeListChatModel(responses=["背景已调查", "数据已分析", "总结已完成"])
    finalizer = FakeListChatModel(responses=["研究报告完成"])

    result = run_plan_execute(
        planner_llm=planner,
        executor_llm=executor,
        finalizer_llm=finalizer,
        user_input="写一份研究报告",
    )
    assert len(result["plan"]) == 3
    assert result["final_answer"] == "研究报告完成"


@pytest.mark.fast
def test_plan_parse_numbered_list() -> None:
    """planner 输出编号列表应被正确解析。"""
    planner = FakeListChatModel(responses=["1. 步骤一\n2. 步骤二\n3. 步骤三"])
    executor = FakeListChatModel(responses=["r1", "r2", "r3"])
    finalizer = FakeListChatModel(responses=["done"])

    result = run_plan_execute(
        planner_llm=planner,
        executor_llm=executor,
        finalizer_llm=finalizer,
        user_input="任务",
    )
    assert result["plan"] == ["步骤一", "步骤二", "步骤三"]


@pytest.mark.fast
def test_plan_execute_with_prebuilt() -> None:
    """对比 agent_core.build_plan_execute_graph 的输出。"""
    from agent_core import AgentRuntime, build_plan_execute_graph

    planner = FakeListChatModel(responses=["1. 一\n2. 二"])
    executor = FakeListChatModel(responses=["r1", "r2"])
    finalizer = FakeListChatModel(responses=["done"])
    runtime = AgentRuntime(
        build_plan_execute_graph(
            planner_llm=planner, executor_llm=executor, finalizer_llm=finalizer
        )
    )
    out = runtime.invoke({"messages": [HumanMessage(content="task")]})
    assert out["plan"] == ["一", "二"]
    assert out["final_answer"] == "done"
