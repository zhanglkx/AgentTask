# 第 1 章：LLM 与开发环境基础

> 从零开始理解 LLM 核心概念，用 LangChain 调通第一个模型，掌握 token 计费。

## 本章目标

- 理解 LLM 基础概念：token / temperature / context window / 角色（system / user / assistant）
- 掌握 `uv` 工具链与项目结构
- 第一次调用 LLM（从 HTTP → SDK → LangChain 逐步升级）
- 学会 token 计费计算

## 前端工程师对照

| LLM 概念 | 前端类比 |
|---|---|
| Token | 字符编码（UTF-8 code point），但粒度更粗——一个 token ≈ 0.75 个英文单词 |
| Temperature | `Math.random()` 的分布宽度——0 = 确定性输出，1 = 最大随机性 |
| Context Window | 内存限制——像浏览器的 `heap size`，超出就截断 |
| System Prompt | `<meta>` 标签——全局配置，对所有后续内容生效 |
| User / Assistant | HTTP request / response——交替对话，与 WebSocket 双向通信类似 |

## 产出

1. `src/hello_llm.py` —— LLM 调用的最小封装
2. `src/cost_calculator.py` —— token 计费工具
3. `notebook.ipynb` —— 5 个 cell 交互式探索

## 依赖

- `common/config.Settings`
- `llm_providers/factory.get_chat_model()`
- `common/cost.CostTracker`

## 快速开始

```bash
# 跑本章测试
uv run pytest lessons/01-foundations/tests/ -m fast

# 跑 notebook
uv run jupyter lab lessons/01-foundations/notebook.ipynb
```
