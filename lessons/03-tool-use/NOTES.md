# 第 3 章小结

## 核心概念

1. **Function Calling 本质**：LLM 输出 `{"name": "add", "args": {"a": 1, "b": 2}}` → 你执行函数 → 把结果作为 ToolMessage 喂回
2. **手写循环**：while loop——调 LLM → 有 tool_calls 就执行 → 没有就结束
3. **@tool 装饰器**：给函数加元数据（name / description / schema），自动注册到全局表
4. **Tool Schema**：从函数签名自动生成 JSON schema（等价于 OpenAPI spec）

## 进阶阅读

- [LangChain Tool Calling](https://python.langchain.com/docs/concepts/tool_calling/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
