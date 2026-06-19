# 第 2 章：提示工程与结构化输出

> 学会用 Pydantic（≈ Zod）让 LLM 输出结构化数据，掌握 prompt 模板与思维链。

## 本章目标

- 理解 Zero-shot / Few-shot / CoT / Self-Consistency 提示策略
- 掌握 Pydantic（≈ Zod for Python）定义输出 schema
- 学会 `with_structured_output()` 让 LLM 返回结构化对象
- 掌握 `ChatPromptTemplate` / `MessagesPlaceholder`

## 前端工程师对照

| Python 概念 | JS/TS 对应 |
|---|---|
| Pydantic BaseModel | Zod schema / TypeScript interface |
| `with_structured_output()` | AI SDK `generateObject()` |
| ChatPromptTemplate | 模板字符串 + 变量注入 |
| CoT (Chain of Thought) | "Let's think step by step" ≈ 分步调试 |
| Few-shot | Jest snapshot 测试——给 LLM 看示例再让它输出 |

## 产出

1. `src/structured_extractor.py` —— 结构化抽取（Person / Company / Event）
2. `src/prompt_template_demo.py` —— ChatPromptTemplate 示例
3. `notebook.ipynb` —— 交互式探索

## 快速开始

```bash
uv run pytest lessons/02-prompting-and-structured-output/tests/ -m fast
```
