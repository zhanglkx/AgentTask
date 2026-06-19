# 第 4 章：ReAct 模式

> LangGraph 入门——手写 ReAct graph vs prebuilt `build_react_graph`，通过同一道测试题验证等价性。

## 本章目标

- 理解 ReAct 论文核心：Reasoning + Acting 交替循环
- 入门 LangGraph：`StateGraph` / `add_node` / `add_conditional_edges`
- **手写 ReAct graph**（用 StateGraph 自建）
- **对比手写版 vs `agent_core.build_react_graph` prebuilt 版**
- 验收：两版通过同一道测试题（spec §9.M2 关键验收点）

## 前端工程师对照

| ReAct / LangGraph 概念 | 前端类比 |
|---|---|
| StateGraph | Redux store + reducer——状态驱动的有向图 |
| add_node | 注册一个 reducer function |
| add_conditional_edges | `switch` 语句——根据 state 选择下一路径 |
| add_messages reducer | Redux reducer——合并新旧消息列表 |
| ReAct 循环 | while loop：思考 → 行动 → 观察 → 思考 → ... → 回答 |
| `build_react_graph` | `createReducer()` 预制——封装了标准模式 |

## 产出

1. `src/hand_coded_react.py` —— 手写 ReAct graph
2. `src/prebuilt_react.py` —— 用 `agent_core.build_react_graph`
3. `tests/shared_cases.py` —— SHARED_TEST_CASES（跨实现验证）
4. `tests/test_cross_implementation.py` —— **核心验收**
5. `notebook.ipynb` —— 交互式探索

## 快速开始

```bash
uv run pytest lessons/04-react/tests/ -m fast
```
