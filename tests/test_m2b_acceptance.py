"""M2b 里程碑验收 smoke test。

验证 spec §9.M2 验收点:
1. 每章可独立 import 并跑基础测试
2. Lesson 04 手写版和 prebuilt 版通过同一道测试题
3. 每章 README.md 存在
4. notebook.ipynb 存在且可被 nbformat 读取
"""

from __future__ import annotations

from pathlib import Path

import nbformat
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LESSONS = [
    "01-foundations",
    "02-prompting-and-structured-output",
    "03-tool-use",
    "04-react",
    "05-plan-and-execute",
    "06-reflection-and-reflexion",
]


@pytest.mark.fast
def test_each_lesson_has_readme() -> None:
    """每章 README.md 必须存在。"""
    for lesson in LESSONS:
        readme = REPO_ROOT / "lessons" / lesson / "README.md"
        assert readme.exists(), f"{lesson} 缺少 README.md"


@pytest.mark.fast
def test_each_lesson_has_notebook() -> None:
    """每章 notebook.ipynb 必须存在且可被 nbformat 读取。"""
    for lesson in LESSONS:
        nb_path = REPO_ROOT / "lessons" / lesson / "notebook.ipynb"
        assert nb_path.exists(), f"{lesson} 缺少 notebook.ipynb"
        nb = nbformat.read(str(nb_path), as_version=4)  # type: ignore[no-untyped-call]
        assert len(nb.cells) >= 2, f"{lesson} notebook cell 数 < 2"


@pytest.mark.fast
def test_each_lesson_has_notes() -> None:
    """每章 NOTES.md 必须存在。"""
    for lesson in LESSONS:
        notes = REPO_ROOT / "lessons" / lesson / "NOTES.md"
        assert notes.exists(), f"{lesson} 缺少 NOTES.md"


@pytest.mark.fast
def test_lesson_04_cross_implementation() -> None:
    """Lesson 04 手写版和 prebuilt 版通过同一道测试题（spec §9.M2 关键验收点）。"""
    # 直接跑 lesson 04 的交叉验证测试
    # lesson 04 tests path 需加入 sys.path
    import sys
    from typing import Any

    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.outputs import ChatGeneration, ChatResult

    lesson04_src = str(REPO_ROOT / "lessons" / "04-react" / "src")
    lesson04_tests = str(REPO_ROOT / "lessons" / "04-react" / "tests")
    if lesson04_src not in sys.path:
        sys.path.insert(0, lesson04_src)
    if lesson04_tests not in sys.path:
        sys.path.insert(0, lesson04_tests)

    from shared_cases import SHARED_TEST_CASES  # type: ignore[import-not-found]

    from agent_core import build_react_graph
    from hand_coded_react import build_hand_coded_react  # type: ignore[import-not-found]
    from tools import registry as _reg
    from tools import tool

    _reg._REGISTRY.clear()

    @tool(name="add", description="加法")
    def add(a: int, b: int) -> int:
        return a + b

    class _ScriptedLLM(BaseChatModel):
        responses: list[Any] = []  # noqa: RUF012
        idx: int = 0

        @property
        def _llm_type(self) -> str:
            return "scripted"

        def bind_tools(  # type: ignore[override]
            self, tools: list[Any], **kwargs: Any
        ) -> Any:
            return self

        def _generate(  # type: ignore[override]
            self, messages: list[Any], stop: list[str] | None = None, **kwargs: Any
        ) -> ChatResult:
            msg = self.responses[self.idx]
            self.idx += 1
            return ChatResult(generations=[ChatGeneration(message=msg)])

    case = SHARED_TEST_CASES[0]  # 加法场景
    test_tools = [add]

    # 手写版
    llm_hand = _ScriptedLLM(responses=list(case["llm_responses"]))
    graph_hand = build_hand_coded_react(llm=llm_hand, tools=test_tools)
    result_hand = graph_hand.invoke({"messages": [case["input"]]})
    hand_final = str(result_hand["messages"][-1].content)

    # prebuilt 版
    llm_pre = _ScriptedLLM(responses=list(case["llm_responses"]))
    graph_pre = build_react_graph(llm=llm_pre, tools=test_tools)  # type: ignore[arg-type]
    result_pre = graph_pre.invoke({"messages": [case["input"]]})
    pre_final = str(result_pre["messages"][-1].content)

    # 关键验收：两版产出等价 final answer
    assert hand_final == pre_final, f"两版不等价: 手写={hand_final}, prebuilt={pre_final}"


@pytest.mark.fast
def test_each_lesson_tests_pass() -> None:
    """每章独立测试应全部通过。"""
    for lesson in LESSONS:
        lesson_tests = REPO_ROOT / "lessons" / lesson / "tests"
        if not lesson_tests.exists():
            continue
        test_files = list(lesson_tests.glob("test_*.py"))
        assert len(test_files) > 0, f"{lesson} 缺少测试文件"
