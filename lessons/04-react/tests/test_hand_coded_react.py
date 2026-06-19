"""hand_coded_react 测试：手写 ReAct graph 验证。"""

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from shared_cases import SHARED_TEST_CASES

from tools import tool


class _ScriptedLLM(BaseChatModel):
    responses: list[Any] = []  # noqa: RUF012
    idx: int = 0

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(  # type: ignore[override]
        self,
        tools: list[Any],
        **kwargs: Any,
    ) -> Any:
        return self

    def _generate(
        self,
        messages: list[Any],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        msg = self.responses[self.idx]
        self.idx += 1
        return ChatResult(generations=[ChatGeneration(message=msg)])


@pytest.fixture(autouse=True)
def _clear_registry() -> None:
    from tools import registry as _reg

    _reg._REGISTRY.clear()


@pytest.mark.fast
def test_hand_coded_react_addition() -> None:
    """手写 ReAct: 加法场景。"""

    @tool(name="add", description="加法")
    def add(a: int, b: int) -> int:
        return a + b

    from hand_coded_react import build_hand_coded_react

    llm = _ScriptedLLM(
        responses=[
            AIMessage(
                content="",
                tool_calls=[{"name": "add", "args": {"a": 3, "b": 4}, "id": "c1"}],
            ),
            AIMessage(content="3 + 4 = 7"),
        ]
    )
    graph = build_hand_coded_react(llm=llm, tools=[add])
    result = graph.invoke({"messages": [SHARED_TEST_CASES[0]["input"]]})
    assert SHARED_TEST_CASES[0]["expected_answer"] in str(result["messages"][-1].content)


@pytest.mark.fast
def test_hand_coded_react_weather() -> None:
    """手写 ReAct: 天气查询场景。"""

    @tool(name="weather", description="天气查询")
    def weather(city: str) -> str:
        return f"{city}: 25°C, sunny"

    from hand_coded_react import build_hand_coded_react

    case = SHARED_TEST_CASES[1]
    llm = _ScriptedLLM(responses=case["llm_responses"])
    graph = build_hand_coded_react(llm=llm, tools=[weather])
    result = graph.invoke({"messages": [case["input"]]})
    assert case["expected_answer"] in str(result["messages"][-1].content)


@pytest.mark.fast
def test_hand_coded_react_multi_step() -> None:
    """手写 ReAct: 多步推理场景。"""

    @tool(name="mul", description="乘法")
    def mul(a: int, b: int) -> int:
        return a * b

    @tool(name="add", description="加法")
    def add(a: int, b: int) -> int:
        return a + b

    from hand_coded_react import build_hand_coded_react

    case = SHARED_TEST_CASES[2]
    llm = _ScriptedLLM(responses=case["llm_responses"])
    graph = build_hand_coded_react(llm=llm, tools=[mul, add])
    result = graph.invoke({"messages": [case["input"]]})
    assert case["expected_answer"] in str(result["messages"][-1].content)
