"""OpenAI provider。"""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI

from common.config import get_settings
from common.errors import ConfigError

DEFAULT_MODEL = "gpt-4o-mini"


def build_openai_chat(
    *,
    model: str | None = None,
    temperature: float = 0.7,
    **kwargs: Any,
) -> ChatOpenAI:
    """构造 OpenAI chat 模型。

    Raises:
        ConfigError: 未配置 AGENTTASK_OPENAI_API_KEY。
    """
    settings = get_settings(reload=True)
    if settings.openai_api_key is None:
        raise ConfigError(
            "missing AGENTTASK_OPENAI_API_KEY",
            context={"provider": "openai"},
        )
    return ChatOpenAI(
        model=model or DEFAULT_MODEL,
        temperature=temperature,
        api_key=settings.openai_api_key,
        **kwargs,
    )


__all__ = ["DEFAULT_MODEL", "build_openai_chat"]
