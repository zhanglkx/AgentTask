"""LLM 调用的最小封装。

演示:
- call_llm: 单次调用 LLM,返回文本
- stream_llm: 流式调用,yield token
"""

from __future__ import annotations

from collections.abc import Iterator

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage


def call_llm(
    llm: BaseChatModel,
    user_input: str,
    *,
    system_prompt: str | None = None,
) -> str:
    """单次调用 LLM,返回 AI 的文本响应。

    Args:
        llm: 任意 LangChain BaseChatModel。
        user_input: 用户输入文本。
        system_prompt: 可选的系统提示。

    Returns:
        AI 的文本响应。
    """
    messages: list[SystemMessage | HumanMessage] = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=user_input))
    response = llm.invoke(messages)
    return str(response.content)


def stream_llm(
    llm: BaseChatModel,
    user_input: str,
) -> Iterator[str]:
    """流式调用 LLM,yield token。

    Args:
        llm: 任意 LangChain BaseChatModel（需支持 stream）。
        user_input: 用户输入文本。

    Returns:
        token 字符串的迭代器。
    """
    for chunk in llm.stream([HumanMessage(content=user_input)]):
        if chunk.content:
            yield str(chunk.content)
