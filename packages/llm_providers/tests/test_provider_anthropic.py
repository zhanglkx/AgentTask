"""Anthropic provider 工厂测试。"""

from __future__ import annotations

import pytest
from langchain_anthropic import ChatAnthropic

from common.errors import ConfigError
from llm_providers.providers.anthropic import build_anthropic_chat


@pytest.mark.fast
def test_build_anthropic_returns_chat_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_ANTHROPIC_API_KEY", "sk-ant-test")  # pragma: allowlist secret
    llm = build_anthropic_chat(model="claude-sonnet-4-6", temperature=0.2)
    assert isinstance(llm, ChatAnthropic)
    assert llm.model == "claude-sonnet-4-6"


@pytest.mark.fast
def test_build_anthropic_missing_key_raises() -> None:
    with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
        build_anthropic_chat(model="claude-sonnet-4-6")


@pytest.mark.fast
def test_build_anthropic_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_ANTHROPIC_API_KEY", "sk-ant-test")  # pragma: allowlist secret
    llm = build_anthropic_chat()
    assert llm.model == "claude-sonnet-4-6"
