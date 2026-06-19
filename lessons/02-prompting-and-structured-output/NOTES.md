# 第 2 章小结

## 核心概念

1. **Pydantic ≈ Zod**：用 Python class 定义数据 schema，自动生成 JSON schema 给 LLM
2. **structured output**：`with_structured_output()` 让 LLM 返回 Pydantic 对象而非纯文本
3. **ChatPromptTemplate**：可复用的 prompt 模板，支持变量注入和消息占位
4. **CoT**：引导 LLM "分步思考"提升推理质量

## 进阶阅读

- [Pydantic v2 文档](https://docs.pydantic.dev/)
- [LangChain Structured Output](https://python.langchain.com/docs/concepts/structured_outputs/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
