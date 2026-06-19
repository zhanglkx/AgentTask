"""M2a 里程碑验收 smoke test。

验证 spec §9.M2 验收点:
1. tools 注册表 + 一个 builtin tool 可调
2. 4 种 pattern graph 都能用 fake LLM 跑通至少一道用例
3. AgentRuntime 能产出 AgentEvent 流
4. checkpointer 工厂在 dev 环境返回 MemorySaver
"""

from __future__ import annotations

from typing import Any

import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from agent_core import (
    AgentRuntime,
    EventType,
    InMemoryExperienceStore,
    build_plan_execute_graph,
    build_react_graph,
    build_reflection_graph,
    build_reflexion_graph,
    get_checkpointer,
)
from tools import get_tool, list_tools, tool


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
def _clear_registry() -> Any:
    from tools import registry as _reg

    _reg._REGISTRY.clear()
    yield
    _reg._REGISTRY.clear()


@pytest.mark.fast
def test_tool_registry_roundtrip() -> None:
    @tool(name="double", description="x")
    def double(x: int) -> int:
        return x * 2

    assert get_tool("double") is double
    assert any(t.name == "double" for t in list_tools())
    assert double.run({"x": 5}) == 10


@pytest.mark.fast
def test_react_pattern_smoke() -> None:
    @tool(name="add", description="加法")
    def add(a: int, b: int) -> int:
        return a + b

    llm = _ScriptedLLM(
        responses=[
            AIMessage(
                content="",
                tool_calls=[{"name": "add", "args": {"a": 1, "b": 2}, "id": "c1"}],
            ),
            AIMessage(content="3"),
        ]
    )
    runtime = AgentRuntime(build_react_graph(llm=llm, tools=[add]))
    out = runtime.invoke({"messages": [HumanMessage(content="1+2?")]})
    assert "3" in str(out["messages"][-1].content)


@pytest.mark.fast
def test_plan_execute_pattern_smoke() -> None:
    planner = FakeListChatModel(responses=["1. 一\n2. 二"])
    executor = FakeListChatModel(responses=["r1", "r2"])
    finalizer = FakeListChatModel(responses=["done"])
    runtime = AgentRuntime(
        build_plan_execute_graph(
            planner_llm=planner, executor_llm=executor, finalizer_llm=finalizer
        )
    )
    out = runtime.invoke({"messages": [HumanMessage(content="task")]})
    assert out["plan"] == ["一", "二"]
    assert out["final_answer"] == "done"


@pytest.mark.fast
def test_reflection_pattern_smoke() -> None:
    gen = FakeListChatModel(responses=["v1"])
    crit = FakeListChatModel(responses=["good. ACCEPT"])
    runtime = AgentRuntime(
        build_reflection_graph(generator_llm=gen, critic_llm=crit, max_iterations=3)
    )
    out = runtime.invoke({"messages": [HumanMessage(content="任务")]})
    assert out["final"] == "v1"


@pytest.mark.fast
def test_reflexion_pattern_smoke() -> None:
    actor = FakeListChatModel(responses=["a1"])
    crit = FakeListChatModel(responses=["SUCCESS"])
    store = InMemoryExperienceStore()
    runtime = AgentRuntime(
        build_reflexion_graph(actor_llm=actor, critic_llm=crit, store=store, max_iterations=3)
    )
    out = runtime.invoke({"messages": [HumanMessage(content="任务")]})
    assert "a1" in out["attempt"]


@pytest.mark.fast
async def test_runtime_astream_yields_events() -> None:
    llm = FakeListChatModel(responses=["hi back"])
    runtime = AgentRuntime(build_react_graph(llm=llm, tools=[]))
    events = [e async for e in runtime.astream({"messages": [HumanMessage(content="hi")]})]
    types = {e.type for e in events}
    assert EventType.DONE in types


@pytest.mark.fast
def test_checkpointer_dev_factory() -> None:
    from langgraph.checkpoint.memory import MemorySaver

    cp = get_checkpointer(env="dev")
    assert isinstance(cp, MemorySaver)


@pytest.mark.fast
def test_m2a_demo_script_main_callable() -> None:
    """examples/m2a_react_demo.py 必须可被 import 且 main 可调。"""
    import importlib.util
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    demo = repo_root / "examples" / "m2a_react_demo.py"
    assert demo.exists()
    spec = importlib.util.spec_from_file_location("m2a_demo", demo)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)
