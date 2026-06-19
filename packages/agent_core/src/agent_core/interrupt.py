"""HITL interrupt 包装。

LangGraph 0.2.x 提供 `langgraph.types.interrupt` 原语,允许 node 暂停 graph
并把控制权交还 caller,等 caller 提供 resume 值后再继续。

本模块在它之上加一层语义化 API,统一 payload 结构(便于前端按 reason 分类
渲染审批 UI)。M4 第 12 章会接前端 SSE + Vercel AI SDK。
"""

from __future__ import annotations

from typing import Any

from langgraph.types import interrupt as _interrupt


def request_interrupt(
    *,
    reason: str,
    payload: dict[str, Any] | None = None,
) -> Any:
    """暂停 graph,把 reason + payload 交给 caller 决定如何 resume。

    Args:
        reason: 中断语义("approve_tool_call" / "edit_plan" / ...)。
        payload: 给前端渲染需要的上下文。

    Returns:
        Any: caller 通过 Command(resume=...) 传入的值。
    """
    return _interrupt({"reason": reason, "payload": payload or {}})


__all__ = ["request_interrupt"]
