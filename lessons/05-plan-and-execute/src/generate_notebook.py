"""程序化生成第 5 章 notebook。"""

from __future__ import annotations

from pathlib import Path

import nbformat

LESSON_DIR = Path(__file__).resolve().parent.parent
OUTPUT = LESSON_DIR / "notebook.ipynb"


def main() -> int:
    nb = nbformat.v4.new_notebook()

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="# 第 5 章：Plan-and-Execute 模式\n\n"
            "双 agent 协作——planner 制定计划，executor 逐步执行。\n\n"
            "对比 ReAct：简单交互用 ReAct，复杂研究用 Plan-Execute。"
        )
    )

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="## 5.1 Plan-Execute vs ReAct\n\n"
            "| 方面 | ReAct | Plan-Execute |\n"
            "|---|---|---|\n"
            "| 规划 | 无（边想边做） | 先规划再执行 |\n"
            "| 执行 | 单循环 | 可并行 |\n"
            "| 适用 | 简单交互 | 复杂研究 |\n"
            "| 类比 | 单线程 | 多线程 + 项目经理 |\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_code_cell(
            source="from langchain_community.chat_models.fake import FakeListChatModel\n"
            "from langchain_core.messages import HumanMessage\n"
            "\n"
            "from plan_execute_agent import run_plan_execute\n\n\n"
            "planner = FakeListChatModel(responses=['1. 调查背景\\n2. 分析数据\\n3. 写总结'])\n"
            "executor = FakeListChatModel(responses=['背景已调查', '数据已分析', '总结已完成'])\n"
            "finalizer = FakeListChatModel(responses=['研究报告完成'])\n\n\n"
            "result = run_plan_execute(planner, executor, finalizer, '写一份研究报告')\n"
            "print(f'计划: {result[\"plan\"]}')\n"
            "print(f'最终答案: {result[\"final_answer\"]}')\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="## 5.2 Plan DAG\n\n"
            "Plan DAG 是计划的有向无环图——某些步骤可并行执行。\n\n"
            "类比前端：React useEffect 的依赖数组——deps 不满足就等待，满足就执行。\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_code_cell(
            source="from plan_dag import PlanDAG, PlanStep\n\n"
            "dag = PlanDAG()\n"
            "dag.add_step(PlanStep(id='s1', name='调查A', dependencies=[]))\n"
            "dag.add_step(PlanStep(id='s2', name='调查B', dependencies=[]))\n"
            "dag.add_step(PlanStep(id='s3', name='汇总', dependencies=['s1', 's2']))\n\n\n"
            "print(f'执行顺序: {dag.execution_order()}')\n"
            "# s1 和 s2 可并行, s3 必在两者之后\n"
        )
    )

    nbformat.write(nb, str(OUTPUT))
    print(f"notebook 已生成: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
