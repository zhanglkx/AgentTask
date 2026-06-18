"""Redis 缓存装饰器测试。使用 fakeredis 避免依赖真实 Redis。"""

from __future__ import annotations

from typing import Any

import fakeredis
import pytest

from common.cache import cached, make_cache_key


class _Counter:
    def __init__(self) -> None:
        self.calls = 0


@pytest.fixture
def fake_redis() -> fakeredis.FakeRedis:
    return fakeredis.FakeRedis(decode_responses=False)


@pytest.mark.fast
def test_make_cache_key_is_deterministic() -> None:
    """同样的输入应得到同样的 key。"""
    k1 = make_cache_key("namespace", "model-x", {"prompt": "hello", "temp": 0.7})
    k2 = make_cache_key("namespace", "model-x", {"temp": 0.7, "prompt": "hello"})
    assert k1 == k2
    assert k1.startswith("namespace:")


@pytest.mark.fast
def test_make_cache_key_changes_with_input() -> None:
    """输入不同 → key 不同。"""
    k1 = make_cache_key("ns", "m", {"prompt": "a"})
    k2 = make_cache_key("ns", "m", {"prompt": "b"})
    assert k1 != k2


@pytest.mark.fast
def test_cached_first_call_executes_function(fake_redis: fakeredis.FakeRedis) -> None:
    """首次调用应执行函数并写缓存。"""
    counter = _Counter()

    @cached(client=fake_redis, namespace="t", ttl_seconds=60)
    def expensive(x: int) -> dict[str, int]:
        counter.calls += 1
        return {"value": x * 2}

    result = expensive(5)
    assert result == {"value": 10}
    assert counter.calls == 1


@pytest.mark.fast
def test_cached_second_call_hits_cache(fake_redis: fakeredis.FakeRedis) -> None:
    """同样参数的第二次调用应直接返回缓存,不执行函数体。"""
    counter = _Counter()

    @cached(client=fake_redis, namespace="t", ttl_seconds=60)
    def expensive(x: int) -> dict[str, int]:
        counter.calls += 1
        return {"value": x * 2}

    expensive(5)
    expensive(5)
    expensive(5)
    assert counter.calls == 1


@pytest.mark.fast
def test_cached_different_args_dont_collide(fake_redis: fakeredis.FakeRedis) -> None:
    """不同参数应得到不同缓存项。"""
    counter = _Counter()

    @cached(client=fake_redis, namespace="t", ttl_seconds=60)
    def expensive(x: int) -> int:
        counter.calls += 1
        return x * 2

    assert expensive(1) == 2
    assert expensive(2) == 4
    assert expensive(3) == 6
    assert counter.calls == 3


@pytest.mark.fast
def test_cached_supports_complex_jsonable_return(fake_redis: fakeredis.FakeRedis) -> None:
    """支持 list/dict/str/int/float/bool/None 的 JSON 序列化返回值。"""
    counter = _Counter()

    @cached(client=fake_redis, namespace="t", ttl_seconds=60)
    def fancy() -> dict[str, Any]:
        counter.calls += 1
        return {"items": [1, 2, 3], "meta": {"name": "x", "ok": True}}

    fancy()
    fancy()
    assert counter.calls == 1


@pytest.mark.fast
async def test_cached_async_function(fake_redis: fakeredis.FakeRedis) -> None:
    """装饰器应同时支持 async 函数。"""
    counter = _Counter()

    @cached(client=fake_redis, namespace="t", ttl_seconds=60)
    async def aget(x: int) -> int:
        counter.calls += 1
        return x + 100

    assert await aget(1) == 101
    assert await aget(1) == 101
    assert counter.calls == 1


@pytest.mark.fast
def test_cached_ttl_expires(fake_redis: fakeredis.FakeRedis) -> None:
    """TTL 过期后应重新执行函数。"""
    counter = _Counter()

    @cached(client=fake_redis, namespace="t", ttl_seconds=1)
    def f() -> int:
        counter.calls += 1
        return 42

    f()
    assert fake_redis.delete(*fake_redis.keys("t:*"))
    f()
    assert counter.calls == 2
