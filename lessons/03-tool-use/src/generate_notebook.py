"""程序化生成第 3 章 notebook。"""

from __future__ import annotations

from pathlib import Path

import nbformat

LESSON_DIR = Path(__file__).resolve().parent.parent
OUTPUT = LESSON_DIR / "notebook.ipynb"


def main() -> int:
    nb = nbformat.v4.new_notebook()

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="# 第 3 章：工具调用（Tool Use）\n\n"
            "理解 function calling 本质，手写工具循环看清底层机制。"
        )
    )

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="## 3.1 Function Calling 本质\n\n"
            "LLM 不是直接执行代码，而是输出一个 JSON 指令：\n\n"
            "```json\n"
            '{"name": "add", "args": {"a": 1, "b": 2}}\n'
            "```\n\n"
            "你（开发者）执行函数 → 把结果喂回 LLM → LLM 给最终答案。\n\n"
            "类比前端：LLM 是 HTTP client，你的函数是 server。"
        )
    )

    nb.cells.append(
        nbformat.v4.new_code_cell(
            source="from tools import tool, get_tool, list_tools\n\n\n"
            "@tool(name='add', description='把两个整数相加')\n"
            "def add(a: int, b: int) -> int:\n"
            "    return a + b\n\n\n"
            "# @tool 自动注册到全局表 + 自动生成 JSON schema\n"
            "print(f'注册的工具: {[t.name for t in list_tools()]}')\n"
            "print(f'add 的 schema: {add.args_schema.model_json_schema()}')\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="## 3.2 手写工具循环\n\n"
            "不用 LangGraph——看清底层 while-loop：\n\n"
            "```python\n"
            "while True:\n"
            "    ai_msg = llm.invoke(messages)\n"
            "    if not ai_msg.tool_calls:  # 无工具调用 → 最终答案\n"
            "        break\n"
            "    for tc in ai_msg.tool_calls:  # 执行每个工具\n"
            "        result = run_tool(tc)\n"
            "        messages.append(ToolMessage(content=str(result)))\n"
            "```\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_code_cell(
            source="from langchain_core.messages import AIMessage, ToolMessage\n"
            "from langchain_core.language_models.chat_models import BaseChatModel\n"
            "from langchain_core.outputs import ChatGeneration, ChatResult\n"
            "from typing import Any\n\n\n"
            "class _ScriptedLLM(BaseChatModel):\n"
            "    responses: list[Any] = []  # noqa: RUF012\n"
            "    idx: int = 0\n\n"
            "    @property\n"
            "    def _llm_type(self) -> str:\n"
            "        return 'scripted'\n\n"
            "    def bind_tools(self, tools: list[Any], **kwargs: Any) -> Any:  # type: ignore[override]\n"
            "        return self\n\n"
            "    def _generate(self, messages: list[Any], stop: list[str] | None = None, **kwargs: Any) -> ChatResult:\n"
            "        msg = self.responses[self.idx]\n"
            "        self.idx += 1\n"
            "        return ChatResult(generations=[ChatGeneration(message=msg)])\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_code_cell(
            source="from tool_loop import run_tool_loop\n\n\n"
            "# 模拟: 第一轮调 add(3,4), 第二轮给最终答案\n"
            "llm = _ScriptedLLM(\n"
            "    responses=[\n"
            "        AIMessage(content='', tool_calls=[{'name': 'add', 'args': {'a': 3, 'b': 4}, 'id': 'c1'}]),\n"
            "        AIMessage(content='3 + 4 = 7'),\n"
            "    ],\n"
            ")\n\n"
            "@tool(name='add', description='加法')\n"
            "def add(a: int, b: int) -> int:\n"
            "    return a + b\n\n\n"
            "result = run_tool_loop(llm, '算 3+4', [add])\n"
            "print(f'最终答案: {result[-1].content}')\n"
        )
    )

    nbformat.write(nb, str(OUTPUT))
    print(f"notebook 已生成: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
