# 第 6 章：Reflection 与 Reflexion 模式

> 让 Agent 自我批评与改进——写作 agent 写 → critic → 修订，coding agent 写 → 跑测试 → 修订。

## 本章目标

- 理解 Basic Reflection：生成 → 批判 → 修订循环
- 理解 Reflexion：在 Reflection 基础上加经验记忆（episodic memory）
- 掌握 critique-revise 模式与准确率对比基线
- 实现写作 agent + coding agent 雏形

## 前端工程师对照

| Reflection 概念 | 前端类比 |
|---|---|
| Generator | Feature developer——写初版代码 |
| Critic | Code reviewer——指出问题 |
| Accept marker | CI passing——"可以合并了" |
| ExperienceStore | Git log——记住过去经验，下次做得更好 |
| Reflexion | Agile retrospective——从失败中学习 |

## 产出

1. `src/writing_agent.py` —— 写 → critic → 修订
2. `src/coding_agent.py` —— 写 → 跑测试 → 修订（雏形）
3. `notebook.ipynb` —— 交互式探索

## 快速开始

```bash
uv run pytest lessons/06-reflection-and-reflexion/tests/ -m fast
```
