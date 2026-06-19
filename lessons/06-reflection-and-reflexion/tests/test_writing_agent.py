"""writing_agent 测试：写 → critic → 修订。"""

from __future__ import annotations

import pytest
from langchain_community.chat_models.fake import FakeListChatModel

from writing_agent import run_writing_agent


@pytest.mark.fast
def test_writing_agent_accept_on_first_try() -> None:
    """critic 第一次就 ACCEPT → 直接返回 draft。"""
    gen = FakeListChatModel(responses=["初稿很好"])
    crit = FakeListChatModel(responses=["ACCEPT"])

    result = run_writing_agent(
        generator_llm=gen,
        critic_llm=crit,
        task="写一段介绍",
        max_iterations=3,
    )
    assert result["final"] == "初稿很好"


@pytest.mark.fast
def test_writing_agent_revise_then_accept() -> None:
    """critic 第一次 REJECT → 修订 → 第二次 ACCEPT。"""
    gen = FakeListChatModel(responses=["v1", "v2（改进版）"])
    crit = FakeListChatModel(responses=["需要改进", "ACCEPT"])

    result = run_writing_agent(
        generator_llm=gen,
        critic_llm=crit,
        task="写一段介绍",
        max_iterations=3,
    )
    assert result["final"] == "v2（改进版）"


@pytest.mark.fast
def test_writing_agent_with_prebuilt() -> None:
    """对比 agent_core.build_reflection_graph。"""
    from agent_core import AgentRuntime, build_reflection_graph

    gen = FakeListChatModel(responses=["v1"])
    crit = FakeListChatModel(responses=["good. ACCEPT"])
    runtime = AgentRuntime(
        build_reflection_graph(generator_llm=gen, critic_llm=crit, max_iterations=3)
    )
    from langchain_core.messages import HumanMessage

    out = runtime.invoke({"messages": [HumanMessage(content="任务")]})
    assert out["final"] == "v1"


@pytest.mark.fast
def test_writing_agent_max_iterations() -> None:
    """超过 max_iterations 时返回最后一次 draft。"""
    gen = FakeListChatModel(responses=["v1", "v2", "v3"])
    crit = FakeListChatModel(responses=["需要改进", "还是不行", "依然不行"])

    result = run_writing_agent(
        generator_llm=gen,
        critic_llm=crit,
        task="写一段介绍",
        max_iterations=2,
    )
    assert result["final"] == "v2"
