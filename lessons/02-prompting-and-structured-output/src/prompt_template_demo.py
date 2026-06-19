"""Prompt 模板演示：ChatPromptTemplate / MessagesPlaceholder。

类比前端:
    - ChatPromptTemplate ≈ 模板字符串 + 变量注入（像 JSX props）
    - MessagesPlaceholder ≈ React slot（动态插入子组件）
    - format_prompt ≈ template literal（`Hello ${name}!`）
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage


def format_prompt(template: str, variables: dict[str, str]) -> str:
    """把变量注入模板字符串并返回结果。

    Args:
        template: 包含 {variable} 占位符的模板字符串。
        variables: 变量名到值的映射。

    Returns:
        注入变量后的字符串。
    """
    return template.format(**variables)


def build_messages(
    user_input: str,
    *,
    system_prompt: str | None = None,
) -> list[SystemMessage | HumanMessage]:
    """构建消息列表（system + user）。

    Args:
        user_input: 用户输入。
        system_prompt: 可选的系统提示。

    Returns:
        消息列表。
    """
    messages: list[SystemMessage | HumanMessage] = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=user_input))
    return messages
