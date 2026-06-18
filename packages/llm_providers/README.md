# llm_providers

统一封装四个 LLM provider,提供同一 LangChain `BaseChatModel` 接口:
DeepSeek（默认）/ Anthropic / OpenAI / Ollama（本地）。

## 使用

```python
from llm_providers import get_chat_model

# 用配置中的默认 provider 与默认 model
llm = get_chat_model()

# 显式指定
llm = get_chat_model(provider="anthropic", model="claude-sonnet-4-6")

# 切到本地 Ollama
llm = get_chat_model(provider="ollama", model="llama3.2")

response = llm.invoke("hello")
```

切换 provider 不需要改业务代码 —— 这就是本包存在的意义。

## 模块

| 模块 | 作用 |
|---|---|
| `factory.get_chat_model` | 总入口,按 provider 分发 |
| `providers/{deepseek,anthropic,openai,ollama}.py` | 各 provider 工厂函数 |
| `middleware` | with_cost_tracking / with_cache 包装器 |
| `embeddings.get_embeddings` | embedding 工厂（OpenAI / Ollama） |
