"""统一工厂 get_chat_model 测试。"""

from __future__ import annotations

import pytest
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from common.errors import ConfigError
from llm_providers import get_chat_model


@pytest.mark.fast
def test_default_provider_is_deepseek(monkeypatch: pytest.MonkeyPatch) -> None:
    """无参数时,使用 Settings.default_llm_provider（默认 deepseek）。"""
    monkeypatch.setenv("AGENTTASK_DEEPSEEK_API_KEY", "sk-test")  # pragma: allowlist secret
    llm = get_chat_model()
    assert isinstance(llm, ChatOpenAI)
    assert "deepseek.com" in str(llm.openai_api_base or "")


@pytest.mark.fast
def test_explicit_provider_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_ANTHROPIC_API_KEY", "sk-ant-test")  # pragma: allowlist secret
    llm = get_chat_model(provider="anthropic", model="claude-sonnet-4-6")
    assert isinstance(llm, ChatAnthropic)


@pytest.mark.fast
def test_explicit_provider_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_OPENAI_API_KEY", "sk-openai-test")  # pragma: allowlist secret
    llm = get_chat_model(provider="openai", model="gpt-4o-mini")
    assert isinstance(llm, ChatOpenAI)


@pytest.mark.fast
def test_explicit_provider_ollama() -> None:
    llm = get_chat_model(provider="ollama", model="llama3.2")
    assert isinstance(llm, ChatOllama)


@pytest.mark.fast
def test_default_provider_via_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """AGENTTASK_DEFAULT_LLM_PROVIDER=ollama → get_chat_model() 返回 Ollama。"""
    monkeypatch.setenv("AGENTTASK_DEFAULT_LLM_PROVIDER", "ollama")
    llm = get_chat_model()
    assert isinstance(llm, ChatOllama)


@pytest.mark.fast
def test_unknown_provider_raises() -> None:
    """未知 provider 应抛 ConfigError。"""
    with pytest.raises(ConfigError, match="unknown provider"):
        get_chat_model(provider="not-a-real-provider")


@pytest.mark.fast
def test_temperature_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    """temperature 参数应透传到 provider。"""
    monkeypatch.setenv("AGENTTASK_DEEPSEEK_API_KEY", "sk-test")  # pragma: allowlist secret
    llm = get_chat_model(temperature=0.0)
    assert llm.temperature == 0.0  # type: ignore[attr-defined]
