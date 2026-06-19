"""hello_llm 测试：fake LLM 调用验证。"""

from __future__ import annotations

import pytest
from langchain_community.chat_models.fake import FakeListChatModel

from hello_llm import call_llm, stream_llm


@pytest.mark.fast
def test_call_llm_returns_str() -> None:
    """call_llm 应返回 LLM 的文本响应。"""
    llm = FakeListChatModel(responses=["你好！"])
    result = call_llm(llm, "hi")
    assert result == "你好！"


@pytest.mark.fast
def test_call_llm_with_system_prompt() -> None:
    """带 system_prompt 调 LLM 应把 system prompt 拼进 messages。"""
    llm = FakeListChatModel(responses=["角色已接受"])
    result = call_llm(llm, "你好", system_prompt="你是数学老师")
    assert result == "角色已接受"


@pytest.mark.fast
def test_stream_llm_yields_tokens() -> None:
    """stream_llm 应 yield token 串。"""
    llm = FakeListChatModel(responses=["逐字输出"])
    tokens = list(stream_llm(llm, "开始"))
    assert len(tokens) > 0
