"""Ollama provider（本地）。无需 API key。"""

from __future__ import annotations

from typing import Any

from langchain_ollama import ChatOllama

from common.config import get_settings

DEFAULT_MODEL = "llama3.2"


def build_ollama_chat(
    *,
    model: str | None = None,
    temperature: float = 0.7,
    **kwargs: Any,
) -> ChatOllama:
    """构造 Ollama chat 模型。base_url 来自 Settings.ollama_base_url。"""
    settings = get_settings(reload=True)
    return ChatOllama(
        model=model or DEFAULT_MODEL,
        temperature=temperature,
        base_url=settings.ollama_base_url,
        **kwargs,
    )


__all__ = ["DEFAULT_MODEL", "build_ollama_chat"]
