"""prebuilt_react 测试：用 agent_core.build_react_graph。"""

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatGeneration, ChatResult
from shared_cases import SHARED_TEST_CASES

from agent_core import build_react_graph
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
def test_prebuilt_react_addition() -> None:
    """prebuilt ReAct: 加法场景。"""

    @tool(name="add", description="加法")
    def add(a: int, b: int) -> int:
        return a + b

    case = SHARED_TEST_CASES[0]
    llm = _ScriptedLLM(responses=case["llm_responses"])
    graph = build_react_graph(llm=llm, tools=[add])
    result = graph.invoke({"messages": [case["input"]]})
    assert case["expected_answer"] in str(result["messages"][-1].content)


@pytest.mark.fast
def test_prebuilt_react_weather() -> None:
    """prebuilt ReAct: 天气查询场景。"""

    @tool(name="weather", description="天气查询")
    def weather(city: str) -> str:
        return f"{city}: 25°C, sunny"

    case = SHARED_TEST_CASES[1]
    llm = _ScriptedLLM(responses=case["llm_responses"])
    graph = build_react_graph(llm=llm, tools=[weather])
    result = graph.invoke({"messages": [case["input"]]})
    assert case["expected_answer"] in str(result["messages"][-1].content)


@pytest.mark.fast
def test_prebuilt_react_multi_step() -> None:
    """prebuilt ReAct: 多步推理场景。"""

    @tool(name="mul", description="乘法")
    def mul(a: int, b: int) -> int:
        return a * b

    @tool(name="add", description="加法")
    def add(a: int, b: int) -> int:
        return a + b

    case = SHARED_TEST_CASES[2]
    llm = _ScriptedLLM(responses=case["llm_responses"])
    graph = build_react_graph(llm=llm, tools=[mul, add])
    result = graph.invoke({"messages": [case["input"]]})
    assert case["expected_answer"] in str(result["messages"][-1].content)
