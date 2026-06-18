"""错误类层级行为测试。"""

from __future__ import annotations

import pytest

from common.errors import (
    AgentError,
    BudgetExceededError,
    ConfigError,
    LLMError,
    RateLimitError,
    RetryableError,
    ToolError,
)


@pytest.mark.fast
def test_agent_error_is_base_class() -> None:
    """所有自定义错误都应继承 AgentError。"""
    for cls in (
        LLMError,
        ToolError,
        RetryableError,
        RateLimitError,
        BudgetExceededError,
        ConfigError,
    ):
        assert issubclass(cls, AgentError), f"{cls.__name__} 必须继承 AgentError"


@pytest.mark.fast
def test_rate_limit_is_retryable() -> None:
    """RateLimitError 应同时是 RetryableError（用于重试装饰器分流）。"""
    assert issubclass(RateLimitError, RetryableError)


@pytest.mark.fast
def test_agent_error_carries_context() -> None:
    """AgentError 必须支持 context dict,用于日志结构化。"""
    err = AgentError("something failed", context={"agent": "researcher", "step": 3})
    assert err.context == {"agent": "researcher", "step": 3}
    assert "something failed" in str(err)


@pytest.mark.fast
def test_agent_error_default_context_empty() -> None:
    """未传 context 时默认为空 dict（避免 None 判断）。"""
    err = AgentError("oops")
    assert err.context == {}


@pytest.mark.fast
def test_llm_error_records_provider_and_model() -> None:
    """LLMError 必须记录 provider 与 model,便于 trace。"""
    err = LLMError("api 503", provider="deepseek", model="deepseek-chat")
    assert err.provider == "deepseek"
    assert err.model == "deepseek-chat"
    assert err.context["provider"] == "deepseek"
    assert err.context["model"] == "deepseek-chat"


@pytest.mark.fast
def test_budget_exceeded_records_amounts() -> None:
    """BudgetExceededError 必须记录 spent / limit 数值。"""
    err = BudgetExceededError(spent_usd=12.34, limit_usd=10.0)
    assert err.spent_usd == 12.34
    assert err.limit_usd == 10.0
    assert "12.34" in str(err)
    assert "10.0" in str(err)


@pytest.mark.fast
def test_tool_error_carries_tool_name() -> None:
    """ToolError 必须记录工具名。"""
    err = ToolError("permission denied", tool_name="shell")
    assert err.tool_name == "shell"
    assert err.context["tool_name"] == "shell"
