"""统一错误类层级。

设计原则:
- AgentError 是顶层基类,所有 agent 系统抛出的错误都应继承它。
- RetryableError 表示"可重试"语义,装饰器据此决定是否退避重试。
- 非 RetryableError 的错误立刻向上抛,不重试。
- 每个错误都带 context dict,用于日志/trace 结构化输出。
"""

from __future__ import annotations

from typing import Any


class AgentError(Exception):
    """所有 agent 系统错误的基类。

    Args:
        message: 人类可读的错误说明。
        context: 结构化上下文字段（agent / tool / step 等）,用于日志。
    """

    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.context: dict[str, Any] = dict(context) if context else {}


class ConfigError(AgentError):
    """配置错误（缺失环境变量、格式错等）。不可重试。"""


class RetryableError(AgentError):
    """标记型基类:继承自此的错误会被 retry 装饰器视为"应重试"。"""


class RateLimitError(RetryableError):
    """LLM/外部 API 限流。属于可重试错误。"""


class LLMError(AgentError):
    """LLM 调用错误（非限流）。

    Args:
        message: 错误说明。
        provider: LLM provider 名（deepseek / anthropic / openai / ollama）。
        model: 具体模型名。
        context: 额外上下文。
    """

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        model: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        merged: dict[str, Any] = {"provider": provider, "model": model}
        if context:
            merged.update(context)
        super().__init__(message, context=merged)
        self.provider = provider
        self.model = model


class ToolError(AgentError):
    """工具调用错误。

    Args:
        message: 错误说明。
        tool_name: 工具名（与 @tool 装饰器注册的名字一致）。
        context: 额外上下文。
    """

    def __init__(
        self,
        message: str,
        *,
        tool_name: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        merged: dict[str, Any] = {"tool_name": tool_name}
        if context:
            merged.update(context)
        super().__init__(message, context=merged)
        self.tool_name = tool_name


class BudgetExceededError(AgentError):
    """成本超出预算。

    Args:
        spent_usd: 已花费金额。
        limit_usd: 预算上限。
    """

    def __init__(
        self,
        *,
        spent_usd: float,
        limit_usd: float,
        context: dict[str, Any] | None = None,
    ) -> None:
        merged: dict[str, Any] = {"spent_usd": spent_usd, "limit_usd": limit_usd}
        if context:
            merged.update(context)
        message = f"budget exceeded: spent {spent_usd} USD > limit {limit_usd} USD"
        super().__init__(message, context=merged)
        self.spent_usd = spent_usd
        self.limit_usd = limit_usd
