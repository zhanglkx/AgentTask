"""OpenAI provider 工厂测试。"""

from __future__ import annotations

import pytest
from langchain_openai import ChatOpenAI

from common.errors import ConfigError
from llm_providers.providers.openai import build_openai_chat


@pytest.mark.fast
def test_build_openai_returns_chat_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_OPENAI_API_KEY", "sk-openai-test")  # pragma: allowlist secret
    llm = build_openai_chat(model="gpt-4o-mini", temperature=0.0)
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "gpt-4o-mini"


@pytest.mark.fast
def test_build_openai_missing_key_raises() -> None:
    with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
        build_openai_chat(model="gpt-4o-mini")


@pytest.mark.fast
def test_build_openai_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_OPENAI_API_KEY", "sk-openai-test")  # pragma: allowlist secret
    llm = build_openai_chat()
    assert llm.model_name == "gpt-4o-mini"
