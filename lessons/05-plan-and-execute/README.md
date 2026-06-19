# 第 5 章：Plan-and-Execute 模式

> 双 agent 协作——planner 制定计划，executor 逐步执行，对比 ReAct 选型。

## 本章目标

- 理解 Plan-and-Execute 模式：先规划再执行，可动态 replan
- 掌握 planner / executor 双 agent 设计
- 理解 Plan DAG（计划的有向无环图表示）
- 对比 ReAct vs Plan-Execute 选型决策

## 前端工程师对照

| Plan-Execute 概念 | 前端类比 |
|---|---|
| Planner agent | 项目经理——拆任务 |
| Executor agent | 开发者——逐个完成 |
| Plan DAG | 依赖图——Task A → Task B → Task C |
| Replan | Sprint replanning——发现 blocker 时调整计划 |
| Finalizer | QA review——汇总所有结果出终版 |

## 产出

1. `src/plan_execute_agent.py` —— 手写 plan-execute agent
2. `src/plan_dag.py` —— plan DAG 结构（纯 Python dict）
3. `notebook.ipynb` —— 交互式探索

## 快速开始

```bash
uv run pytest lessons/05-plan-and-execute/tests/ -m fast
```
