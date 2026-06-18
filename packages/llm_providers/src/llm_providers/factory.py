"""统一 chat model 工厂。

`get_chat_model(provider=None, model=None, **kwargs)` 是业务代码访问 LLM 的唯一入口。
provider=None 时走 Settings.default_llm_provider,model=None 时各 provider 用自己的默认值。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from common.config import get_settings
from common.errors import ConfigError

from .providers.anthropic import build_anthropic_chat
from .providers.deepseek import build_deepseek_chat
from .providers.ollama import build_ollama_chat
from .providers.openai import build_openai_chat

_BUILDERS: dict[str, Callable[..., BaseChatModel]] = {
    "deepseek": build_deepseek_chat,
    "anthropic": build_anthropic_chat,
    "openai": build_openai_chat,
    "ollama": build_ollama_chat,
}


def get_chat_model(
    *,
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    **kwargs: Any,
) -> BaseChatModel:
    """构造一个 LangChain BaseChatModel。

    Args:
        provider: deepseek / anthropic / openai / ollama。None 时读 Settings 默认。
        model: 具体模型名。None 时各 provider 用 DEFAULT_MODEL。
        temperature: 采样温度。
        **kwargs: 透传给底层 provider 工厂。

    Raises:
        ConfigError: provider 名称未注册或对应 API key 缺失。
    """
    chosen = (provider or get_settings(reload=True).default_llm_provider).lower()
    builder = _BUILDERS.get(chosen)
    if builder is None:
        raise ConfigError(
            f"unknown provider: {chosen!r}; expected one of {sorted(_BUILDERS)}",
            context={"provider": chosen},
        )
    return builder(model=model, temperature=temperature, **kwargs)


__all__ = ["get_chat_model"]
