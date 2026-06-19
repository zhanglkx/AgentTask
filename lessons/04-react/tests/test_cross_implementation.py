"""交叉验证测试：手写版与 prebuilt 版通过同一道测试题。

这是 spec §9.M2 关键验收点:
    "agent_core/patterns/react 与第 4 章手写版本通过同一道测试题"
"""

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatGeneration, ChatResult
from shared_cases import SHARED_TEST_CASES

from agent_core import build_react_graph
from hand_coded_react import build_hand_coded_react
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


def _make_tools_for_case(case: dict[str, Any]) -> list[Any]:
    """从测试用例的 tool_specs 创建工具列表。"""
    tools_list: list[Any] = []

    @tool(name="add", description="加法")
    def add(a: int, b: int) -> int:
        return a + b

    @tool(name="mul", description="乘法")
    def mul(a: int, b: int) -> int:
        return a * b

    @tool(name="weather", description="天气查询")
    def weather(city: str) -> str:
        return f"{city}: 25°C, sunny"

    for spec in case["tool_specs"]:
        if spec["name"] == "add":
            tools_list.append(add)
        elif spec["name"] == "mul":
            tools_list.append(mul)
        elif spec["name"] == "weather":
            tools_list.append(weather)

    return tools_list


@pytest.mark.fast
@pytest.mark.parametrize("case", SHARED_TEST_CASES, ids=lambda c: c["name"])
def test_hand_coded_and_prebuilt_produce_same_answer(case: dict[str, Any]) -> None:
    """核心验收: 手写版和 prebuilt 版对同一 input 产出等价 final answer。"""
    test_tools = _make_tools_for_case(case)

    # 手写版
    llm_hand = _ScriptedLLM(responses=list(case["llm_responses"]))
    graph_hand = build_hand_coded_react(llm=llm_hand, tools=test_tools)
    result_hand = graph_hand.invoke({"messages": [case["input"]]})
    hand_final = str(result_hand["messages"][-1].content)

    # prebuilt 版
    llm_pre = _ScriptedLLM(responses=list(case["llm_responses"]))
    graph_pre = build_react_graph(llm=llm_pre, tools=test_tools)
    result_pre = graph_pre.invoke({"messages": [case["input"]]})
    pre_final = str(result_pre["messages"][-1].content)

    # 两版都应包含 expected_answer
    assert case["expected_answer"] in hand_final, f"手写版失败: {hand_final}"
    assert case["expected_answer"] in pre_final, f"prebuilt版失败: {pre_final}"

    # 两版 final answer 文本应等价
    assert hand_final == pre_final, f"两版不等价: 手写={hand_final}, prebuilt={pre_final}"
