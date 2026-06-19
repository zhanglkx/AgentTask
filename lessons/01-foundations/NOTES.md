# 第 1 章小结

## 核心概念

1. **Token**：LLM 的最小文本单位，1 token ≈ 0.75 英文单词，中文约 1-2 字/token
2. **Temperature**：控制输出随机性，0 = 确定性，1 = 最大创意
3. **Context Window**：模型一次能处理的 token 总量（输入 + 输出）
4. **角色**：system（全局指令）、user（用户输入）、assistant（模型输出）

## 计费公式

```
cost = input_tokens × price_per_input_token + output_tokens × price_per_output_token
```

## 进阶阅读

- [LangChain 官方文档：Chat Models](https://python.langchain.com/docs/concepts/chat_models/)
- [DeepSeek API 文档](https://api-docs.deepseek.com/)
- [OpenAI Token 计算器](https://platform.openai.com/tokenizer)
