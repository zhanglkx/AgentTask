"""手写工具循环：不用 LangGraph，看清底层机制。

核心思路:
    while True:
        ai_msg = llm.invoke(messages)
        if not ai_msg.tool_calls:  # LLM 不再要调工具 → 返回最终答案
            break
        for tc in ai_msg.tool_calls:  # 执行每个 tool call
            result = run_tool(tc.name, tc.args)
            messages.append(ToolMessage(...))  # 把结果喂回 LLM

类比前端:
    这就像 WebSocket 双向通信循环——消息 → 处理 → 回消息 → 循环。
    LangGraph 的 build_react_graph 就是把这个循环封装成 graph。
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, ToolMessage


def _find_tool(name: str, tools: list[Any]) -> Any:
    """根据名称在工具列表中查找工具。"""
    for t in tools:
        if t.name == name:
            return t
    raise ValueError(f"未知工具: {name}")


def run_tool_loop(
    llm: BaseChatModel,
    user_input: str,
    tools: list[Any],
    *,
    max_iterations: int = 10,
) -> list[Any]:
    """手写工具循环：调 LLM → 有 tool_calls 就执行 → 喂回 → 循环 → 直到无 tool_calls。

    Args:
        llm: 任意 LangChain BaseChatModel（需支持 tool calling）。
        user_input: 用户输入。
        tools: BaseTool 列表。
        max_iterations: 安全限制，防止无限循环。

    Returns:
        所有消息列表（包括最终回答）。
    """
    bound_llm = llm.bind_tools(tools) if tools else llm
    messages: list[Any] = [HumanMessage(content=user_input)]

    for _ in range(max_iterations):
        ai_msg = bound_llm.invoke(messages)
        messages.append(ai_msg)

        # 无 tool_calls → LLM 给了最终回答，循环结束
        tool_calls = getattr(ai_msg, "tool_calls", None)
        if not tool_calls:
            break

        # 执行每个 tool call 并把结果喂回
        for tc in tool_calls:
            tool_obj = _find_tool(tc["name"], tools)
            result = tool_obj.run(tc["args"])
            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tc["id"],
                )
            )

    return messages
