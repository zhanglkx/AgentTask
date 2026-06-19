"""M2a 验收 demo:用 fake LLM 跑通 ReAct 完整循环。

运行方式:
    uv run python examples/m2a_react_demo.py

输出包含:tool 被调 → 拿结果 → AI 给最终答 三类信息。
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from agent_core import AgentRuntime, build_react_graph
from common.logging import configure_logging, get_logger
from tools import tool


class _ScriptedLLM(BaseChatModel):
    """Demo 用脚本化 LLM:第一轮发 tool_call,第二轮发最终答。"""

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


def main() -> int:
    configure_logging(level="INFO")
    log = get_logger("m2a.demo")

    @tool(name="add", description="把两个整数相加。")
    def add(a: int, b: int) -> int:
        return a + b

    llm = _ScriptedLLM(
        responses=[
            AIMessage(
                content="",
                tool_calls=[{"name": "add", "args": {"a": 7, "b": 5}, "id": "c1"}],
            ),
            AIMessage(content="7 + 5 = 12。"),
        ]
    )

    graph = build_react_graph(llm=llm, tools=[add])
    runtime = AgentRuntime(graph)
    out = runtime.invoke({"messages": [HumanMessage(content="算 7+5")]})

    log.info(
        "demo_done",
        message_count=len(out["messages"]),
        final=str(out["messages"][-1].content),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
