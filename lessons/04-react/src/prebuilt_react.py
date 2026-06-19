"""prebuilt ReAct：用 agent_core.build_react_graph 一行调用。

对比手写版（hand_coded_react.py）:
    - 手写版: 自己 add_node / add_conditional_edges,看清每一步
    - prebuilt 版: build_react_graph(llm, tools),封装了标准模式

两者等价——这是 spec §9.M2 关键验收点。
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool

from agent_core import build_react_graph


def build_prebuilt_react(
    *,
    llm: BaseChatModel,
    tools: list[BaseTool],
    system_prompt: str | None = None,
) -> Any:
    """用 agent_core 的 prebuilt ReAct graph。

    Args:
        llm: 任意 LangChain BaseChatModel。
        tools: BaseTool 列表。
        system_prompt: 可选系统提示。

    Returns:
        编译后的 StateGraph（与手写版等价）。
    """
    return build_react_graph(llm=llm, tools=tools, system_prompt=system_prompt)
