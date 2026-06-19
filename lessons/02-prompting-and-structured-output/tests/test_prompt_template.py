"""prompt_template_demo 测试：ChatPromptTemplate 用法。"""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from prompt_template_demo import build_messages, format_prompt


@pytest.mark.fast
def test_format_prompt_returns_str() -> None:
    """format_prompt 应把变量注入模板并返回字符串。"""
    result = format_prompt(template="你好 {name}！", variables={"name": "张三"})
    assert result == "你好 张三！"


@pytest.mark.fast
def test_build_messages_with_system_prompt() -> None:
    """build_messages 应返回包含 system + user 的消息列表。"""
    msgs = build_messages(
        system_prompt="你是助手",
        user_input="帮我算题",
    )
    assert len(msgs) == 2
    assert isinstance(msgs[0], SystemMessage)
    assert isinstance(msgs[1], HumanMessage)


@pytest.mark.fast
def test_build_messages_without_system() -> None:
    """不带 system_prompt 时只返回 user 消息。"""
    msgs = build_messages(user_input="hi")
    assert len(msgs) == 1
    assert isinstance(msgs[0], HumanMessage)


@pytest.mark.fast
def test_chat_prompt_template_invoke() -> None:
    """ChatPromptTemplate.invoke 应正确注入变量。"""
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是 {role}"),
            ("human", "{question}"),
        ]
    )
    formatted = prompt.invoke({"role": "数学老师", "question": "1+1=?"})
    assert len(formatted.to_messages()) == 2
