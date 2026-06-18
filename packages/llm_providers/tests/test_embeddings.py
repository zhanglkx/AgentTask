"""embedding 工厂测试。"""

from __future__ import annotations

import pytest
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from common.errors import ConfigError
from llm_providers import get_embeddings


@pytest.mark.fast
def test_get_embeddings_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_OPENAI_API_KEY", "sk-test")  # pragma: allowlist secret
    emb = get_embeddings(provider="openai", model="text-embedding-3-small")
    assert isinstance(emb, OpenAIEmbeddings)
    assert emb.model == "text-embedding-3-small"


@pytest.mark.fast
def test_get_embeddings_openai_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_OPENAI_API_KEY", "sk-test")  # pragma: allowlist secret
    emb = get_embeddings(provider="openai")
    assert emb.model == "text-embedding-3-small"  # type: ignore[attr-defined]


@pytest.mark.fast
def test_get_embeddings_ollama() -> None:
    emb = get_embeddings(provider="ollama", model="nomic-embed-text")
    assert isinstance(emb, OllamaEmbeddings)
    assert emb.model == "nomic-embed-text"


@pytest.mark.fast
def test_get_embeddings_openai_missing_key() -> None:
    with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
        get_embeddings(provider="openai")


@pytest.mark.fast
def test_get_embeddings_unknown_provider() -> None:
    with pytest.raises(ConfigError, match="unknown embedding provider"):
        get_embeddings(provider="anthropic")  # Anthropic 没有 embedding API


@pytest.mark.fast
def test_get_embeddings_default_provider_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    """无 provider 参数时,默认 openai(因为 deepseek/anthropic 都没有 embedding)。"""
    monkeypatch.setenv("AGENTTASK_OPENAI_API_KEY", "sk-test")  # pragma: allowlist secret
    emb = get_embeddings()
    assert isinstance(emb, OpenAIEmbeddings)
