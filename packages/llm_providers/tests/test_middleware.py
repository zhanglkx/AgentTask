"""middleware 包装器测试。

用 FakeListChatModel(LangChain 内置)模拟 LLM,完全本地、无网络。
"""

from __future__ import annotations

import fakeredis
import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.messages import HumanMessage

from common.cost import CostTracker
from llm_providers.middleware import (
    with_cache,
    with_cost_tracking,
)


@pytest.mark.fast
def test_with_cost_tracking_records_after_invoke() -> None:
    """invoke 之后 CostTracker 应记录到这一次调用的 token 数。"""
    fake = FakeListChatModel(responses=["hello world"])
    tracker = CostTracker()
    wrapped = with_cost_tracking(fake, tracker=tracker, model="deepseek-chat")

    response = wrapped.invoke([HumanMessage(content="hi")])

    assert response.content == "hello world"
    # token 数应记录(估算或真实,大于 0 即可)
    assert tracker.total_input_tokens > 0
    assert tracker.total_output_tokens > 0


@pytest.mark.fast
def test_with_cost_tracking_attributes_to_correct_model() -> None:
    """记录应归到传入的 model 名,而非 FakeListChatModel 自己的。"""
    fake = FakeListChatModel(responses=["abc"])
    tracker = CostTracker()
    wrapped = with_cost_tracking(fake, tracker=tracker, model="claude-sonnet-4-6")

    wrapped.invoke([HumanMessage(content="hi")])

    per_model = tracker.per_model()
    assert "claude-sonnet-4-6" in per_model


@pytest.mark.fast
def test_with_cache_first_invoke_executes_underlying() -> None:
    """首次调用应实际调用底层 LLM。"""
    fake = FakeListChatModel(responses=["A", "B"])  # 2 个候选回答
    redis_client = fakeredis.FakeRedis()
    wrapped = with_cache(fake, client=redis_client, namespace="test", ttl_seconds=60)

    response = wrapped.invoke([HumanMessage(content="x")])
    assert response.content == "A"


@pytest.mark.fast
def test_with_cache_second_invoke_hits_cache() -> None:
    """同样 prompt 第二次调用应命中缓存,不消耗底层 LLM 的下一个回答。"""
    fake = FakeListChatModel(responses=["A", "B"])
    redis_client = fakeredis.FakeRedis()
    wrapped = with_cache(fake, client=redis_client, namespace="test", ttl_seconds=60)

    first = wrapped.invoke([HumanMessage(content="x")])
    second = wrapped.invoke([HumanMessage(content="x")])

    assert first.content == second.content == "A"
    # 如果穿透了,第二次应该是 "B",所以下一个不同 prompt 应该拿到 "B"
    third = wrapped.invoke([HumanMessage(content="y")])
    assert third.content == "B"


@pytest.mark.fast
def test_with_cache_different_prompts_dont_collide() -> None:
    """不同 prompt 应各自缓存。"""
    fake = FakeListChatModel(responses=["A", "B", "A-again"])
    redis_client = fakeredis.FakeRedis()
    wrapped = with_cache(fake, client=redis_client, namespace="test", ttl_seconds=60)

    a1 = wrapped.invoke([HumanMessage(content="x")])
    b1 = wrapped.invoke([HumanMessage(content="y")])
    a2 = wrapped.invoke([HumanMessage(content="x")])

    assert a1.content == "A"
    assert b1.content == "B"
    assert a2.content == "A"  # 命中缓存


@pytest.mark.fast
def test_compose_cost_then_cache_does_not_double_count() -> None:
    """先成本追踪、再缓存:同样 prompt 第二次命中缓存时不应再次计数。"""
    fake = FakeListChatModel(responses=["A", "B"])
    redis_client = fakeredis.FakeRedis()
    tracker = CostTracker()

    wrapped = with_cost_tracking(
        with_cache(fake, client=redis_client, namespace="test", ttl_seconds=60),
        tracker=tracker,
        model="deepseek-chat",
    )

    wrapped.invoke([HumanMessage(content="x")])
    tokens_after_first = tracker.total_input_tokens + tracker.total_output_tokens

    wrapped.invoke([HumanMessage(content="x")])  # 缓存命中
    tokens_after_second = tracker.total_input_tokens + tracker.total_output_tokens

    # 缓存命中时,with_cost_tracking 应跳过记账(检测到 cached 标记)
    assert tokens_after_second == tokens_after_first
