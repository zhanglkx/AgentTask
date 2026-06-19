"""程序化生成第 2 章 notebook。"""

from __future__ import annotations

from pathlib import Path

import nbformat

LESSON_DIR = Path(__file__).resolve().parent.parent
OUTPUT = LESSON_DIR / "notebook.ipynb"


def main() -> int:
    nb = nbformat.v4.new_notebook()

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="# 第 2 章：提示工程与结构化输出\n\n"
            "Pydantic ≈ Zod —— 让 LLM 输出结构化数据而非纯文本。"
        )
    )

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="## 2.1 Pydantic ≈ Zod\n\n"
            "前端开发者已经熟悉 Zod schema 验证：\n\n"
            "```typescript\n"
            "const PersonSchema = z.object({\n"
            "  name: z.string(),\n"
            "  age: z.number(),\n"
            "});\n"
            "```\n\n"
            "Python 中等价的是 Pydantic BaseModel：\n\n"
            "```python\n"
            "class Person(BaseModel):\n"
            "    name: str\n"
            "    age: int\n"
            "```\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_code_cell(
            source="from pydantic import BaseModel\n\n\n"
            "class Person(BaseModel):\n"
            "    name: str\n"
            "    age: int\n"
            "    occupation: str\n\n\n"
            "class Company(BaseModel):\n"
            "    name: str\n"
            "    founded: int\n"
            "    industry: str\n\n\n"
            "# Pydantic 自动把 JSON → Python 对象（像 Zod.parse()）\n"
            'p = Person.model_validate_json(\'{"name": "张三", "age": 30, "occupation": "工程师"}\')\n'
            "print(f'{p.name}, {p.age}岁, {p.occupation}')\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="## 2.2 结构化抽取：手写 JSON parse 版\n\n"
            "核心思路：让 LLM 返回 JSON 字符串 → 用 Pydantic 解析。\n\n"
            "这是看清底层的第一步。后面会看到 `with_structured_output()` 自动完成这个过程。"
        )
    )

    nb.cells.append(
        nbformat.v4.new_code_cell(
            source="from langchain_community.chat_models.fake import FakeListChatModel\n"
            "from structured_extractor import extract_with_schema\n\n\n"
            "llm = FakeListChatModel(\n"
            '    responses=[\'{"name": "张三", "age": 30, "occupation": "工程师"}\'],\n'
            ")\n\n"
            "result = extract_with_schema(llm, '张三，30岁，是一名软件工程师。', Person)\n"
            "print(f'抽取结果: {result}')\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="## 2.3 ChatPromptTemplate\n\n"
            "类比前端：\n"
            "- `ChatPromptTemplate` ≈ JSX 模板 + props\n"
            "- `MessagesPlaceholder` ≈ React slot\n\n"
            "把硬编码的字符串变成可复用的模板。"
        )
    )

    nb.cells.append(
        nbformat.v4.new_code_cell(
            source="from langchain_core.prompts import ChatPromptTemplate\n\n\n"
            "# 创建模板（类似 React component）\n"
            "prompt = ChatPromptTemplate.from_messages([\n"
            "    ('system', '你是{role}，只回答{domain}问题。'),\n"
            "    ('human', '{question}'),\n"
            "])\n\n\n"
            "# 注入变量（类似 JSX props）\n"
            "messages = prompt.invoke({'role': '数学老师', 'domain': '数学', 'question': '1+1=?'}).to_messages()\n"
            "print(f'System: {messages[0].content}')\n"
            "print(f'Human: {messages[1].content}')\n"
        )
    )

    nb.cells.append(
        nbformat.v4.new_markdown_cell(
            source="## 2.4 Chain of Thought（思维链）\n\n"
            '类比前端：分步调试——让 LLM "Let\'s think step by step"，\n'
            "就像把一个大函数拆成多个小步骤 debug。"
        )
    )

    nb.cells.append(
        nbformat.v4.new_code_cell(
            source="from langchain_community.chat_models.fake import FakeListChatModel\n\n\n"
            "# CoT: 在 prompt 中要求 LLM 分步推理\n"
            "llm = FakeListChatModel(\n"
            "    responses=['1. 理解问题: 求 17 × 23\\n2. 计算: 17 × 23 = 391\\n3. 答案: 391'],\n"
            ")\n\n"
            "result = llm.invoke('请分步计算 17 × 23')\n"
            "print(result.content)\n"
        )
    )

    nbformat.write(nb, str(OUTPUT))
    print(f"notebook 已生成: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
