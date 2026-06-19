"""coding_agent 测试：写 → 跑测试 → 修订（雏形）。"""

from __future__ import annotations

import pytest
from langchain_community.chat_models.fake import FakeListChatModel

from coding_agent import run_coding_agent


@pytest.mark.fast
def test_coding_agent_success_on_first_try() -> None:
    """测试通过 → SUCCESS → 直接返回代码。"""
    actor = FakeListChatModel(responses=["def add(a, b): return a + b"])
    critic = FakeListChatModel(responses=["SUCCESS"])

    result = run_coding_agent(
        actor_llm=actor,
        critic_llm=critic,
        task="写一个加法函数",
        max_iterations=3,
    )
    assert "add" in result["attempt"]


@pytest.mark.fast
def test_coding_agent_revise_then_success() -> None:
    """测试失败 → 修订 → 第二次成功。"""
    actor = FakeListChatModel(responses=["v1（有bug）", "v2（修复版）"])
    critic = FakeListChatModel(responses=["FAIL: 返回 None", "SUCCESS"])

    result = run_coding_agent(
        actor_llm=actor,
        critic_llm=critic,
        task="写一个加法函数",
        max_iterations=3,
    )
    assert "v2" in result["attempt"]


@pytest.mark.fast
def test_coding_agent_with_reflexion() -> None:
    """对比 agent_core.build_reflexion_graph + InMemoryExperienceStore。"""
    from agent_core import AgentRuntime, InMemoryExperienceStore, build_reflexion_graph

    actor = FakeListChatModel(responses=["a1"])
    critic = FakeListChatModel(responses=["SUCCESS"])
    store = InMemoryExperienceStore()

    runtime = AgentRuntime(
        build_reflexion_graph(actor_llm=actor, critic_llm=critic, store=store, max_iterations=3)
    )
    from langchain_core.messages import HumanMessage

    out = runtime.invoke({"messages": [HumanMessage(content="任务")]})
    assert "a1" in out["attempt"]
