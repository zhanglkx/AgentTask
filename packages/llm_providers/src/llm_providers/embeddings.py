"""Embedding 工厂。

仅支持 openai / ollama —— DeepSeek / Anthropic 不提供 embedding API。
"""

from __future__ import annotations

from typing import Any

from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from common.config import get_settings
from common.errors import ConfigError

DEFAULT_OPENAI_MODEL = "text-embedding-3-small"
DEFAULT_OLLAMA_MODEL = "nomic-embed-text"


def get_embeddings(
    *,
    provider: str = "openai",
    model: str | None = None,
    **kwargs: Any,
) -> Embeddings:
    """构造 embedding 模型。

    Args:
        provider: openai / ollama。默认 openai。
        model: 具体模型名。

    Raises:
        ConfigError: provider 不支持或缺 key。
    """
    settings = get_settings(reload=True)
    chosen = provider.lower()

    if chosen == "openai":
        if settings.openai_api_key is None:
            raise ConfigError(
                "missing AGENTTASK_OPENAI_API_KEY",
                context={"provider": "openai"},
            )
        return OpenAIEmbeddings(
            model=model or DEFAULT_OPENAI_MODEL,
            api_key=settings.openai_api_key,
            **kwargs,
        )

    if chosen == "ollama":
        return OllamaEmbeddings(
            model=model or DEFAULT_OLLAMA_MODEL,
            base_url=settings.ollama_base_url,
            **kwargs,
        )

    raise ConfigError(
        f"unknown embedding provider: {provider!r}; expected one of ['openai', 'ollama']",
        context={"provider": chosen},
    )


__all__ = ["DEFAULT_OLLAMA_MODEL", "DEFAULT_OPENAI_MODEL", "get_embeddings"]
