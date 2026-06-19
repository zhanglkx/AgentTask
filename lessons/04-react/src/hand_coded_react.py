"""手写 ReAct graph：用 StateGraph 自建，看清 LangGraph 底层。

对比 prebuilt 版（agent_core.build_react_graph）:
    - 手写版：自己 add_node / add_conditional_edges，看清每一步
    - prebuilt 版：一行调用，封装了标准模式

两者等价——这是 spec §9.M2 关键验收点。

类比前端:
    - StateGraph ≈ Redux store + reducer
    - add_node ≈ 注册一个 reducer function
    - add_conditional_edges ≈ switch 语句（根据 state 选择路径）
    - add_messages reducer ≈ Redux reducer（合并新旧 state）
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from agent_core.state import ReActState


def _should_continue(state: ReActState) -> str:
    """有 tool_calls → 'tools',否则 → END。"""
    last = state["messages"][-1]
    tool_calls = getattr(last, "tool_calls", None)
    if tool_calls:
        return "tools"
    return END


def build_hand_coded_react(
    *,
    llm: BaseChatModel,
    tools: list[BaseTool],
    system_prompt: str | None = None,
) -> Any:
    """手写 ReAct graph（与 agent_core.build_react_graph 等价）。

    Args:
        llm: 任意 LangChain BaseChatModel。
        tools: BaseTool 列表。
        system_prompt: 可选系统提示。

    Returns:
        编译后的 StateGraph。
    """
    bound_llm = llm.bind_tools(tools) if tools else llm

    def agent_node(state: ReActState) -> dict[str, Any]:
        msgs = list(state["messages"])
        new_msgs: list[Any] = []
        if system_prompt and not any(isinstance(m, SystemMessage) for m in msgs):
            new_msgs.append(SystemMessage(content=system_prompt))
            msgs = [SystemMessage(content=system_prompt), *msgs]
        response = bound_llm.invoke(msgs)
        new_msgs.append(response)
        return {"messages": new_msgs}

    builder = StateGraph(ReActState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", _should_continue, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")
    return builder.compile()
