"""Ollama provider 工厂测试。本地服务,不需要 API key。"""

from __future__ import annotations

import pytest

from llm_providers.providers.ollama import build_ollama_chat


@pytest.mark.fast
def test_build_ollama_returns_chat_ollama() -> None:
    from langchain_ollama import ChatOllama

    llm = build_ollama_chat(model="llama3.2", temperature=0.7)
    assert isinstance(llm, ChatOllama)
    assert llm.model == "llama3.2"


@pytest.mark.fast
def test_build_ollama_default_base_url() -> None:
    llm = build_ollama_chat(model="llama3.2")
    assert "11434" in (llm.base_url or "")


@pytest.mark.fast
def test_build_ollama_custom_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_OLLAMA_BASE_URL", "http://custom-host:11500")
    llm = build_ollama_chat(model="llama3.2")
    assert "custom-host" in (llm.base_url or "")
    assert "11500" in (llm.base_url or "")


@pytest.mark.fast
def test_build_ollama_default_model() -> None:
    llm = build_ollama_chat()
    assert llm.model == "llama3.2"
