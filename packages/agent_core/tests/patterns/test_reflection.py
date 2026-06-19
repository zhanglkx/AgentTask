"""Reflection 模式 graph 测试。"""

from __future__ import annotations

import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.messages import HumanMessage

from agent_core import AgentRuntime
from agent_core.patterns.reflection import build_reflection_graph


@pytest.mark.fast
def test_reflection_accepts_when_critic_signals_accept() -> None:
    """critic 第一轮直接 ACCEPT → 一轮就结束。"""
    gen = FakeListChatModel(responses=["draft v1", "draft v2"])
    crit = FakeListChatModel(responses=["不错。ACCEPT"])
    graph = build_reflection_graph(generator_llm=gen, critic_llm=crit, max_iterations=5)
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="写首四行诗")]})

    assert out["iteration"] == 1
    assert out["final"] == "draft v1"


@pytest.mark.fast
def test_reflection_iterates_until_accept() -> None:
    """前两轮 critic 不满意,第三轮 ACCEPT。"""
    gen = FakeListChatModel(responses=["v1", "v2", "v3"])
    crit = FakeListChatModel(responses=["还要更精炼。", "再短一点。", "完美。ACCEPT"])
    graph = build_reflection_graph(generator_llm=gen, critic_llm=crit, max_iterations=5)
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="x")]})

    assert out["iteration"] == 3
    assert out["final"] == "v3"


@pytest.mark.fast
def test_reflection_respects_max_iterations() -> None:
    """critic 永不 ACCEPT,达到 max_iterations 强制收尾。"""
    gen = FakeListChatModel(responses=["v1", "v2", "v3", "v4"])
    crit = FakeListChatModel(responses=["不行", "不行", "不行", "不行"])
    graph = build_reflection_graph(generator_llm=gen, critic_llm=crit, max_iterations=2)
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="x")]})

    assert out["iteration"] == 2
    assert out["final"] == "v2"
