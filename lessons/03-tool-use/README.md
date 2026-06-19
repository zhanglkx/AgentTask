# 第 3 章：工具调用（Tool Use）

> 理解 function calling 本质，手写工具循环看清底层机制，对比 packages/tools 注册表。

## 本章目标

- 理解 function calling 的本质：LLM 输出 JSON schema → 你执行 → 结果喂回 LLM
- 用 `@tool` 装饰器创建工具，理解 schema 自动生成
- **手写工具循环**（不用 LangGraph，看清底层 while-loop）
- 对比手写实现 vs `packages/tools` 注册表

## 前端工程师对照

| Tool Use 概念 | 前端类比 |
|---|---|
| Function Calling | RPC / API call——LLM 是 client，你的函数是 server |
| Tool Schema | OpenAPI / Swagger spec——描述输入参数和返回值 |
| Tool Loop | WebSocket 双向通信循环——消息 → 处理 → 回消息 → 循环 |
| @tool 装饰器 | React HOC——给普通函数加元数据（schema / name / description） |
| Parallel Tool Calls | Promise.all——LLM 一次发起多个独立调用 |

## 产出

1. `src/tool_loop.py` —— **手写工具循环（核心教学点）**
2. `src/custom_tools.py` —— 5 个自定义工具
3. `notebook.ipynb` —— 交互式探索

## 快速开始

```bash
uv run pytest lessons/03-tool-use/tests/ -m fast
```
