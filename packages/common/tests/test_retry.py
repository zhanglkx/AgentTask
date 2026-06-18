"""tenacity 重试装饰器测试。"""

from __future__ import annotations

import pytest

from common.errors import LLMError, RateLimitError
from common.retry import retry_on_retryable


class _Counter:
    def __init__(self) -> None:
        self.calls = 0


@pytest.mark.fast
def test_retry_succeeds_after_transient_failures() -> None:
    """前 2 次抛 RateLimitError,第 3 次成功 → 装饰器应返回 OK。"""
    c = _Counter()

    @retry_on_retryable(max_attempts=5, initial_wait_s=0.0, max_wait_s=0.0)
    def flaky() -> str:
        c.calls += 1
        if c.calls < 3:
            raise RateLimitError("429")
        return "ok"

    assert flaky() == "ok"
    assert c.calls == 3


@pytest.mark.fast
def test_retry_gives_up_after_max_attempts() -> None:
    """达到 max_attempts 仍失败 → 抛最后一次异常。"""
    c = _Counter()

    @retry_on_retryable(max_attempts=3, initial_wait_s=0.0, max_wait_s=0.0)
    def always_fails() -> None:
        c.calls += 1
        raise RateLimitError("perma 429")

    with pytest.raises(RateLimitError, match="perma 429"):
        always_fails()
    assert c.calls == 3


@pytest.mark.fast
def test_retry_does_not_retry_on_non_retryable() -> None:
    """非 RetryableError → 立刻抛,不重试。"""
    c = _Counter()

    @retry_on_retryable(max_attempts=5, initial_wait_s=0.0, max_wait_s=0.0)
    def boom() -> None:
        c.calls += 1
        raise LLMError("hard error", provider="deepseek", model="deepseek-chat")

    with pytest.raises(LLMError):
        boom()
    assert c.calls == 1


@pytest.mark.fast
def test_retry_does_not_retry_on_value_error() -> None:
    """普通 stdlib 异常也不重试（仅 RetryableError 子类才重试）。"""
    c = _Counter()

    @retry_on_retryable(max_attempts=5, initial_wait_s=0.0, max_wait_s=0.0)
    def bad_input() -> None:
        c.calls += 1
        raise ValueError("nope")

    with pytest.raises(ValueError):
        bad_input()
    assert c.calls == 1


@pytest.mark.fast
async def test_retry_supports_async_function() -> None:
    """装饰器同时支持 async 函数。"""
    c = _Counter()

    @retry_on_retryable(max_attempts=4, initial_wait_s=0.0, max_wait_s=0.0)
    async def flaky_async() -> str:
        c.calls += 1
        if c.calls < 2:
            raise RateLimitError("burst")
        return "done"

    result = await flaky_async()
    assert result == "done"
    assert c.calls == 2
