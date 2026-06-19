"""ReAct 模式 graph 工厂。

形态:
    START → agent → (有 tool_calls?) → tools → agent → ... → END

agent node 调 llm.bind_tools(tools).invoke(messages),
tools node 用 LangGraph ToolNode(自动处理 ToolError)。
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from ..state import ReActState


def _should_continue(state: ReActState) -> str:
    """有 tool_calls → 'tools',否则 → END。"""
    last = state["messages"][-1]
    tool_calls = getattr(last, "tool_calls", None)
    if tool_calls:
        return "tools"
    return END


def build_react_graph(
    *,
    llm: BaseChatModel,
    tools: list[BaseTool],
    system_prompt: str | None = None,
) -> Any:
    """构造 ReAct 模式的 graph(已 compile,未带 checkpointer)。

    Args:
        llm: 任意 LangChain BaseChatModel(实测应支持 tool calling)。
        tools: BaseTool 列表(我们的 Tool 是 BaseTool 子类,直接传)。
        system_prompt: 可选系统提示。
    """
    bound_llm = llm.bind_tools(tools) if tools else llm

    def agent_node(state: ReActState) -> dict[str, Any]:
        msgs = list(state["messages"])
        if system_prompt and not any(isinstance(m, SystemMessage) for m in msgs):
            msgs = [SystemMessage(content=system_prompt), *msgs]
        response = bound_llm.invoke(msgs)
        new_msgs: list[Any] = []
        if system_prompt and not any(isinstance(m, SystemMessage) for m in state["messages"]):
            new_msgs.append(SystemMessage(content=system_prompt))
        new_msgs.append(response)
        return {"messages": new_msgs}

    builder = StateGraph(ReActState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", _should_continue, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")
    return builder.compile()


__all__ = ["build_react_graph"]
