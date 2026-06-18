"""Redis 缓存装饰器。

设计:
- key = namespace + ':' + sha256(stable_repr(args, kwargs))
- value = JSON 序列化的返回值
- 同步与 async 函数都支持
"""

from __future__ import annotations

import asyncio
import functools
import hashlib
import json
from collections.abc import Callable
from typing import Any, TypeVar

import redis

T = TypeVar("T")


def make_cache_key(namespace: str, model: str, payload: dict[str, Any]) -> str:
    """生成稳定的缓存 key:与字典遍历顺序无关。"""
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(f"{model}|{encoded}".encode()).hexdigest()
    return f"{namespace}:{digest}"


def _stable_payload(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    """把任意 args/kwargs 转成 JSON 可序列化的稳定 payload。

    不可 JSON 序列化的对象转 repr(),保证至少能比较等价性。
    """

    def to_jsonable(v: Any) -> Any:
        try:
            json.dumps(v)
        except (TypeError, ValueError):
            return repr(v)
        return v

    return {
        "args": [to_jsonable(a) for a in args],
        "kwargs": {k: to_jsonable(v) for k, v in kwargs.items()},
    }


def cached(
    *,
    client: redis.Redis,
    namespace: str,
    ttl_seconds: int,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """把函数返回值缓存到 Redis。

    Args:
        client: redis-py 客户端（或 fakeredis.FakeRedis,接口兼容）。
        namespace: 缓存 key 前缀,用来区分不同调用点。
        ttl_seconds: 过期秒数。
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                payload = _stable_payload(args, kwargs)
                key = make_cache_key(namespace, func.__qualname__, payload)
                hit: Any = client.get(key)
                if hit is not None:
                    loaded: T = json.loads(hit)
                    return loaded
                result = await func(*args, **kwargs)
                client.setex(key, ttl_seconds, json.dumps(result, ensure_ascii=False))
                return result  # type: ignore[no-any-return]

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            payload = _stable_payload(args, kwargs)
            key = make_cache_key(namespace, func.__qualname__, payload)
            hit: Any = client.get(key)
            if hit is not None:
                loaded: T = json.loads(hit)
                return loaded
            result = func(*args, **kwargs)
            client.setex(key, ttl_seconds, json.dumps(result, ensure_ascii=False))
            return result

        return sync_wrapper

    return decorator


__all__ = ["cached", "make_cache_key"]
