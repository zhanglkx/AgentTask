"""Anthropic provider。"""

from __future__ import annotations

from typing import Any

from langchain_anthropic import ChatAnthropic

from common.config import get_settings
from common.errors import ConfigError

DEFAULT_MODEL = "claude-sonnet-4-6"


def build_anthropic_chat(
    *,
    model: str | None = None,
    temperature: float = 0.7,
    **kwargs: Any,
) -> ChatAnthropic:
    """构造 Anthropic chat 模型。

    Raises:
        ConfigError: 未配置 AGENTTASK_ANTHROPIC_API_KEY。
    """
    settings = get_settings(reload=True)
    if settings.anthropic_api_key is None:
        raise ConfigError(
            "missing AGENTTASK_ANTHROPIC_API_KEY",
            context={"provider": "anthropic"},
        )
    return ChatAnthropic(
        model_name=model or DEFAULT_MODEL,
        temperature=temperature,
        api_key=settings.anthropic_api_key,
        timeout=60,
        stop=None,
        **kwargs,
    )


__all__ = ["DEFAULT_MODEL", "build_anthropic_chat"]
