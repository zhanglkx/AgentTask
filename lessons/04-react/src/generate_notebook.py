"""程序化生成第 4 章 notebook。"""

from __future__ import annotations

from pathlib import Path

import nbformat

LESSON_DIR = Path(__file__).resolve().parent.parent
OUTPUT = LESSON_DIR / "notebook.ipynb"


def main() -> int:
    nb = nbformat.v4.new_notebook()

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="# 第 4 章：ReAct 模式\n\n"
            "LangGraph 入门——手写 ReAct graph vs prebuilt `build_react_graph`。\n\n"
            "**关键验收点**：两版通过同一道测试题（spec §9.M2）。"
        )
    )

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="## 4.1 ReAct 论文核心\n\n"
            "ReAct = **Reasoning** + **Acting** 交替循环：\n\n"
            "1. **思考**（Reasoning）：LLM 分析当前状态\n"
            "2. **行动**（Acting）：调工具获取新信息\n"
            "3. **观察**（Observation）：工具返回的结果\n"
            "4. 循环 1-3 直到得出最终答案\n\n"
            "类比前端：\n"
            "- StateGraph ≈ Redux store + reducer\n"
            "- add_node ≈ 注册 reducer function\n"
            "- add_conditional_edges ≈ switch 语句\n"
            "- add_messages reducer ≈ Redux reducer（合并 state）\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_code_cell(
            source="# 手写 ReAct graph\n"
            "from langgraph.graph import END, START, StateGraph\n"
            "from langgraph.prebuilt import ToolNode\n"
            "from agent_core.state import ReActState\n\n\n"
            "def _should_continue(state: ReActState) -> str:\n"
            "    last = state['messages'][-1]\n"
            "    if getattr(last, 'tool_calls', None):\n"
            "        return 'tools'\n"
            "    return END\n\n\n"
            "builder = StateGraph(ReActState)\n"
            "builder.add_node('agent', ...)  # LLM node\n"
            "builder.add_node('tools', ToolNode(...))  # 工具 node\n"
            "builder.add_edge(START, 'agent')\n"
            "builder.add_conditional_edges('agent', _should_continue)\n"
            "builder.add_edge('tools', 'agent')\n"
            "graph = builder.compile()\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="## 4.2 手写 vs prebuilt 对比\n\n"
            "| 方面 | 手写版 | prebuilt 版 |\n"
            "|---|---|---|\n"
            "| 调用方式 | 自建 StateGraph | `build_react_graph(llm, tools)` |\n"
            "| 理解深度 | 看清每一步 | 封装了标准模式 |\n"
            "| 等价性 | **完全等价** | **完全等价** |\n\n"
            "就像手写 Redux reducer vs `createReducer()`——两者产出相同 state。\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_code_cell(
            source="from hand_coded_react import build_hand_coded_react\n"
            "from prebuilt_react import build_prebuilt_react\n"
            "from agent_core import build_react_graph\n\n\n"
            "# 三种方式产出等价的 graph\n"
            "# graph_hand = build_hand_coded_react(llm=llm, tools=[add])\n"
            "# graph_pre = build_prebuilt_react(llm=llm, tools=[add])\n"
            "# graph_core = build_react_graph(llm=llm, tools=[add])\n\n\n"
            "# 验收: 对同一 input, 三版产出相同 final answer\n"
            "# (详见 tests/test_cross_implementation.py)\n"
        )
    )

    nbformat.write(nb, str(OUTPUT))
    print(f"notebook 已生成: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
