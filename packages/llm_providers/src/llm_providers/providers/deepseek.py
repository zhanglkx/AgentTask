"""DeepSeek provider。

DeepSeek 提供 OpenAI 兼容 API,直接复用 langchain-openai 的 ChatOpenAI,
通过 base_url 指向 https://api.deepseek.com 即可。
"""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI

from common.config import get_settings
from common.errors import ConfigError

DEFAULT_MODEL = "deepseek-chat"


def build_deepseek_chat(
    *,
    model: str | None = None,
    temperature: float = 0.7,
    **kwargs: Any,
) -> ChatOpenAI:
    """构造 DeepSeek chat 模型。

    Args:
        model: 模型名,默认 deepseek-chat。
        temperature: 采样温度。
        **kwargs: 透传给 ChatOpenAI。

    Raises:
        ConfigError: 未配置 AGENTTASK_DEEPSEEK_API_KEY。
    """
    settings = get_settings(reload=True)
    if settings.deepseek_api_key is None:
        raise ConfigError(
            "missing AGENTTASK_DEEPSEEK_API_KEY (set in .env or environment)",
            context={"provider": "deepseek"},
        )
    return ChatOpenAI(
        model=model or DEFAULT_MODEL,
        temperature=temperature,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        **kwargs,
    )


__all__ = ["DEFAULT_MODEL", "build_deepseek_chat"]
