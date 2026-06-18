"""重试策略。

只重试 RetryableError 子类。其他异常（含 LLMError 非限流子类、stdlib 异常）立刻向上抛。
等待策略:指数退避 + jitter。
"""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from typing import TypeVar

from tenacity import (
    AsyncRetrying,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from .errors import RetryableError

T = TypeVar("T")


def retry_on_retryable(
    *,
    max_attempts: int = 5,
    initial_wait_s: float = 1.0,
    max_wait_s: float = 30.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """对函数应用"仅重试 RetryableError"策略,同步与 async 函数都支持。

    Args:
        max_attempts: 最多尝试次数（含首次）。
        initial_wait_s: 第一次失败后的等待基准。
        max_wait_s: 等待时间上限。
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        if asyncio.iscoroutinefunction(func):
            async_retrying = AsyncRetrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_random_exponential(multiplier=initial_wait_s, max=max_wait_s),
                retry=retry_if_exception_type(RetryableError),
                reraise=True,
            )

            @functools.wraps(func)
            async def async_wrapper(*args: object, **kwargs: object) -> T:
                async for attempt in async_retrying:
                    with attempt:
                        return await func(*args, **kwargs)  # type: ignore[no-any-return]
                raise RuntimeError("unreachable")

            return async_wrapper  # type: ignore[return-value]

        sync_retrying = Retrying(
            stop=stop_after_attempt(max_attempts),
            wait=wait_random_exponential(multiplier=initial_wait_s, max=max_wait_s),
            retry=retry_if_exception_type(RetryableError),
            reraise=True,
        )

        @functools.wraps(func)
        def sync_wrapper(*args: object, **kwargs: object) -> T:
            for attempt in sync_retrying:
                with attempt:
                    return func(*args, **kwargs)
            raise RuntimeError("unreachable")

        return sync_wrapper

    return decorator


__all__ = ["retry_on_retryable"]
