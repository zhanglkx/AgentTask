"""程序化生成第 6 章 notebook。"""

from __future__ import annotations

from pathlib import Path

import nbformat

LESSON_DIR = Path(__file__).resolve().parent.parent
OUTPUT = LESSON_DIR / "notebook.ipynb"


def main() -> int:
    nb = nbformat.v4.new_notebook()

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="# 第 6 章：Reflection 与 Reflexion\n\n"
            "让 Agent 自我批评与改进——写作 agent 和 coding agent 雏形。"
        )
    )

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="## 6.1 Basic Reflection\n\n"
            "Reflection = 生成 → 批判 → 修订循环：\n\n"
            "1. **生成**: 写初版\n"
            "2. **批判**: reviewer 指出问题\n"
            "3. **决策**: ACCEPT → 返回,或继续修订\n\n"
            "类比前端：\n"
            "- Generator ≈ Feature developer\n"
            "- Critic ≈ Code reviewer\n"
            "- ACCEPT ≈ CI passing\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_code_cell(
            source="from langchain_community.chat_models.fake import FakeListChatModel\n"
            "from writing_agent import run_writing_agent\n\n\n"
            "gen = FakeListChatModel(responses=['v1', 'v2（改进版）'])\n"
            "crit = FakeListChatModel(responses=['需要改进', 'ACCEPT'])\n\n\n"
            "result = run_writing_agent(gen, crit, '写一段介绍', max_iterations=3)\n"
            "print(f'最终版本: {result[\"final\"]}')\n"
            "print(f'迭代次数: {result[\"iteration\"]}')\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="## 6.2 Reflexion\n\n"
            "Reflexion = Reflection + 经验记忆（episodic memory）：\n\n"
            "1. 从过去的成功/失败中**回忆**（recall）\n"
            "2. 带经验**行动**（act）\n"
            "3. **批判**（critic）\n"
            "4. 如果失败 → **反思**（reflect）并存入经验库\n\n"
            "类比前端：\n"
            "- ExperienceStore ≈ Git log（记住过去经验）\n"
            "- SUCCESS ≈ CI passing\n"
            "- Reflexion ≈ Agile retrospective（从失败中学习）\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_code_cell(
            source="from coding_agent import run_coding_agent\n\n\n"
            "actor = FakeListChatModel(responses=['v1（有bug）', 'v2（修复版）'])\n"
            "critic = FakeListChatModel(responses=['FAIL: 返回 None', 'SUCCESS'])\n\n\n"
            "result = run_coding_agent(actor, critic, '写一个加法函数', max_iterations=3)\n"
            "print(f'最终代码: {result[\"attempt\"]}')\n"
        )
    )

    nbformat.write(nb, str(OUTPUT))
    print(f"notebook 已生成: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
