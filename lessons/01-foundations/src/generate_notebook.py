"""程序化生成第 1 章 notebook。"""

from __future__ import annotations

from pathlib import Path

import nbformat

LESSON_DIR = Path(__file__).resolve().parent.parent  # lessons/01-foundations
OUTPUT = LESSON_DIR / "notebook.ipynb"


def main() -> int:
    nb = nbformat.v4.new_notebook()

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="# 第 1 章：LLM 与开发环境基础\n\n"
            "从零开始理解 LLM 核心概念，用 LangChain 调通第一个模型。"
        )
    )

    # Cell 1: HTTP 调 LLM（概念讲解）
    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="## 1.1 LLM 是什么？\n\n"
            "LLM（Large Language Model）是一个**文本到文本**的函数：\n\n"
            "```python\n"
            "output = llm(input)\n"
            "```\n\n"
            "类比前端：\n"
            "- **Token** ≈ UTF-8 code point，但粒度更粗（1 token ≈ 0.75 英文单词）\n"
            "- **Temperature** ≈ `Math.random()` 的分布宽度（0 = 确定性，1 = 最大随机）\n"
            "- **Context Window** ≈ 浏览器 heap size（超出就截断）\n"
            "- **System Prompt** ≈ `<meta>` 标签（全局配置）\n"
        )
    )

    # Cell 2: 用 LangChain 调 LLM（最小示例）
    nb.cells.append(
        nbformat.v4.new_code_cell(
            source="from langchain_community.chat_models.fake import FakeListChatModel\n\n"
            "llm = FakeListChatModel(responses=['你好！我是你的 AI 助手。'])\n"
            "result = llm.invoke('hello')\n"
            "print(result.content)\n"
        )
    )

    # Cell 3: System Prompt + 多轮对话
    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="## 1.2 System Prompt 与角色\n\n"
            "LLM 有三种角色（类似 HTTP request/response）：\n\n"
            "- **system**：全局指令（`<meta>` 标签）\n"
            "- **user**：用户输入（HTTP request body）\n"
            "- **assistant**：模型输出（HTTP response body）\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_code_cell(
            source="from langchain_community.chat_models.fake import FakeListChatModel\n"
            "from langchain_core.messages import HumanMessage, SystemMessage\n\n"
            "llm = FakeListChatModel(responses=['数学老师已就位', '7 + 5 = 12'])\n\n"
            "# 第一轮：带 system prompt\n"
            "messages = [\n"
            "    SystemMessage(content='你是数学老师，只回答数学问题。'),\n"
            "    HumanMessage(content='你好'),\n"
            "]\n"
            "r1 = llm.invoke(messages)\n"
            "print(f'Round 1: {r1.content}')\n\n"
            "# 第二轮\n"
            "messages = [*messages, r1, HumanMessage(content='7+5=?')]\n"
            "r2 = llm.invoke(messages)\n"
            "print(f'Round 2: {r2.content}')\n"
        )
    )

    # Cell 4: Streaming
    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="## 1.3 Streaming：边想边吐字\n\n"
            "类比前端：WebSocket 推送——LLM 不是一次性返回全文，而是逐 token 流式输出。\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_code_cell(
            source="from langchain_community.chat_models.fake import FakeListChatModel\n\n"
            "llm = FakeListChatModel(responses=['流式输出演示'])\n\n"
            "for chunk in llm.stream('开始'):\n"
            "    if chunk.content:\n"
            "        print(chunk.content, end='', flush=True)\n"
            "print()  # 换行\n"
        )
    )

    # Cell 5: Token 计费
    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="## 1.4 Token 计费\n\n"
            "每个 LLM 调用都消耗 token，计费公式：\n\n"
            "```python\n"
            "cost = input_tokens * price_in + output_tokens * price_out\n"
            "```\n\n"
            "DeepSeek 的价格远低于 GPT-4o——这是选择默认供应商的核心原因。\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_code_cell(
            source="from cost_calculator import PRICING_TABLE, calculate_cost\n\n"
            "# 1000 input tokens + 200 output tokens\n"
            "ds_cost = calculate_cost(1000, 200, PRICING_TABLE['deepseek-chat'])\n"
            "gpt_cost = calculate_cost(1000, 200, PRICING_TABLE['gpt-4o'])\n\n"
            "print(f'DeepSeek: ${ds_cost:.6f}')\n"
            "print(f'GPT-4o:   ${gpt_cost:.6f}')\n"
            "print(f'DeepSeek 比 GPT-4o 便宜 {gpt_cost/ds_cost:.1f} 倍')\n"
        )
    )

    nbformat.write(nb, str(OUTPUT))
    print(f"notebook 已生成: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
