"""DeepSeek provider 工厂测试。

不发起真实 HTTP,只验证返回的 BaseChatModel 配置正确。
"""

from __future__ import annotations

import pytest
from langchain_openai import ChatOpenAI

from common.errors import ConfigError
from llm_providers.providers.deepseek import build_deepseek_chat


@pytest.mark.fast
def test_build_deepseek_returns_chat_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeek 通过 langchain-openai 的 ChatOpenAI + base_url 实现。"""
    monkeypatch.setenv("AGENTTASK_DEEPSEEK_API_KEY", "sk-test")  # pragma: allowlist secret
    llm = build_deepseek_chat(model="deepseek-chat", temperature=0.5)
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "deepseek-chat"
    assert llm.temperature == 0.5
    # base_url 配置在 client 中而非顶层属性,验证 openai_api_base 字段
    assert "deepseek.com" in str(llm.openai_api_base or "")


@pytest.mark.fast
def test_build_deepseek_missing_key_raises() -> None:
    """缺少 API key 应抛 ConfigError。"""
    with pytest.raises(ConfigError, match="DEEPSEEK_API_KEY"):
        build_deepseek_chat(model="deepseek-chat")


@pytest.mark.fast
def test_build_deepseek_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """不传 model 时使用 deepseek-chat。"""
    monkeypatch.setenv("AGENTTASK_DEEPSEEK_API_KEY", "sk-test")  # pragma: allowlist secret
    llm = build_deepseek_chat()
    assert llm.model_name == "deepseek-chat"
