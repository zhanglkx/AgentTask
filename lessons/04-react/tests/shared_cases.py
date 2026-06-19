"""跨实现共享测试用例。

SHARED_TEST_CASES 定义了多组测试输入，
手写版和 prebuilt 版应产出等价的最终答案。

这是 spec §9.M2 关键验收点:
    "agent_core/patterns/react 与第 4 章手写版本通过同一道测试题"
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

# 每个测试用例包含:
# - input: 用户输入 (HumanMessage)
# - llm_responses: _ScriptedLLM 的 responses 列表
# - expected_answer: 最终答案中应包含的文本片段
# - tools: 需注册的工具列表
SHARED_TEST_CASES: list[dict[str, Any]] = [
    {
        "name": "addition",
        "input": HumanMessage(content="算 3+4"),
        "llm_responses": [
            AIMessage(
                content="",
                tool_calls=[{"name": "add", "args": {"a": 3, "b": 4}, "id": "c1"}],
            ),
            AIMessage(content="3 + 4 = 7"),
        ],
        "expected_answer": "7",
        "tool_specs": [
            {"name": "add", "description": "加法", "func": "lambda a, b: a + b"},
        ],
    },
    {
        "name": "weather_query",
        "input": HumanMessage(content="杭州天气怎么样"),
        "llm_responses": [
            AIMessage(
                content="",
                tool_calls=[{"name": "weather", "args": {"city": "杭州"}, "id": "c2"}],
            ),
            AIMessage(content="杭州今天 25°C，晴天"),
        ],
        "expected_answer": "25",
        "tool_specs": [
            {
                "name": "weather",
                "description": "天气查询",
                "func": "lambda city: f'{city}: 25°C, sunny'",
            },
        ],
    },
    {
        "name": "multi_step",
        "input": HumanMessage(content="先算 2×3，再算 6+1"),
        "llm_responses": [
            AIMessage(
                content="",
                tool_calls=[{"name": "mul", "args": {"a": 2, "b": 3}, "id": "c3"}],
            ),
            AIMessage(
                content="",
                tool_calls=[{"name": "add", "args": {"a": 6, "b": 1}, "id": "c4"}],
            ),
            AIMessage(content="2×3=6, 6+1=7"),
        ],
        "expected_answer": "7",
        "tool_specs": [
            {"name": "mul", "description": "乘法", "func": "lambda a, b: a * b"},
            {"name": "add", "description": "加法", "func": "lambda a, b: a + b"},
        ],
    },
]
