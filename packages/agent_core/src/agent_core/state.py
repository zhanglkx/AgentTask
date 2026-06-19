"""Agent state 定义(spec §8.1)。

设计:
- 用 TypedDict + Annotated[T, reducer]。LangGraph 用 reducer 合并并行 / sequential
  node 返回的 partial state。
- BaseAgentState 定义所有 agent 共用的最小字段(messages + error)。
- 每个 pattern 自己的 State 显式继承 BaseAgentState 并扩展业务字段。
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


def add_unique(left: list[str], right: list[str]) -> list[str]:
    """合并两个字符串列表,按首次出现顺序去重。"""
    seen: set[str] = set()
    out: list[str] = []
    for item in [*left, *right]:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


class BaseAgentState(TypedDict, total=False):
    """所有 agent 通用的最小 state。"""

    messages: Annotated[list[BaseMessage], add_messages]
    error: str | None


class ReActState(BaseAgentState):
    """ReAct 模式只需要消息流。"""


class PlanExecuteState(BaseAgentState):
    """Plan-and-Execute 模式。

    plan: 步骤字符串列表
    current_step: 下一个待执行步骤索引
    step_results: 每步的结果(按索引对齐)
    final_answer: 全部完成后的总结
    """

    plan: list[str]
    current_step: int
    step_results: Annotated[list[str], add_unique]
    final_answer: str


class ReflectionState(BaseAgentState):
    """Basic Reflection 模式。

    task: 用户原始任务
    draft: 当前草稿
    critique: 当轮 critic 反馈
    final: 终稿(满意后写入)
    iteration: 已迭代次数
    """

    task: str
    draft: str
    critique: str
    final: str
    iteration: int


class ReflexionState(BaseAgentState):
    """Reflexion 模式(带跨尝试的经验记忆)。

    task: 用户原始任务
    attempt: 本轮尝试结果
    critique: 当轮 critic 反馈
    experiences: 历次失败教训(跨 iteration 累积)
    iteration: 已尝试次数
    """

    task: str
    attempt: str
    critique: str
    experiences: Annotated[list[str], add_unique]
    iteration: int


__all__ = [
    "BaseAgentState",
    "PlanExecuteState",
    "ReActState",
    "ReflectionState",
    "ReflexionState",
    "add_unique",
]
