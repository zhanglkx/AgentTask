"""Reflexion 模式 graph + ExperienceStore 测试。"""

from __future__ import annotations

import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.messages import HumanMessage

from agent_core import AgentRuntime
from agent_core.patterns.reflexion import (
    InMemoryExperienceStore,
    build_reflexion_graph,
)


@pytest.mark.fast
def test_reflexion_in_memory_store_roundtrip() -> None:
    """store.add → store.recall 应能取出。"""
    store = InMemoryExperienceStore()
    store.add(task="t1", experience="lesson A")
    store.add(task="t1", experience="lesson B")
    store.add(task="t2", experience="lesson C")

    assert set(store.recall("t1")) == {"lesson A", "lesson B"}
    assert store.recall("t2") == ["lesson C"]
    assert store.recall("nope") == []


@pytest.mark.fast
def test_reflexion_succeeds_on_first_attempt() -> None:
    """critic 第一轮就 SUCCESS,不需要积累经验。"""
    actor = FakeListChatModel(responses=["attempt 1"])
    crit = FakeListChatModel(responses=["完美。SUCCESS"])
    store = InMemoryExperienceStore()

    graph = build_reflexion_graph(
        actor_llm=actor,
        critic_llm=crit,
        store=store,
        max_iterations=5,
    )
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="任务 X")]})

    assert out["iteration"] == 1
    assert "attempt 1" in out["attempt"]


@pytest.mark.fast
def test_reflexion_accumulates_experiences_across_failures() -> None:
    """前两次失败,critique 进 store;第三次 SUCCESS。store 应有 2 条经验。"""
    actor = FakeListChatModel(responses=["a1", "a2", "a3"])
    crit = FakeListChatModel(
        responses=[
            "不对,缺论据。",
            "还是不行,引用源。",
            "OK。SUCCESS",
        ]
    )
    store = InMemoryExperienceStore()

    graph = build_reflexion_graph(
        actor_llm=actor,
        critic_llm=crit,
        store=store,
        max_iterations=5,
    )
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="任务 Y")]})

    assert out["iteration"] == 3
    recalled = store.recall("任务 Y")
    assert len(recalled) == 2


@pytest.mark.fast
def test_reflexion_recalls_existing_experiences_into_state() -> None:
    """store 已有该 task 的经验,recall 应把它们写入 state.experiences。"""
    store = InMemoryExperienceStore()
    store.add(task="任务 Z", experience="prior lesson 1")
    store.add(task="任务 Z", experience="prior lesson 2")

    actor = FakeListChatModel(responses=["x"])
    crit = FakeListChatModel(responses=["SUCCESS"])

    graph = build_reflexion_graph(actor_llm=actor, critic_llm=crit, store=store, max_iterations=3)
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="任务 Z")]})

    assert set(out["experiences"]) >= {"prior lesson 1", "prior lesson 2"}
