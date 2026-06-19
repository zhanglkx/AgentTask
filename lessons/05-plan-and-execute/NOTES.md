# 第 5 章小结

## 核心概念

1. **Plan-Execute**：先规划（拆分任务）再逐步执行，适合复杂研究类任务
2. **Planner / Executor 分离**：planner 负责拆解，executor 负责逐个完成，职责清晰
3. **Plan DAG**：计划的依赖关系图，支持并行执行独立步骤
4. **Replan**：发现执行结果不理想时动态调整计划
5. **选型**：ReAct 适合简单交互，Plan-Execute 适合复杂研究

## 进阶阅读

- [Plan-and-Execute 论文](https://arxiv.org/abs/2305.04091)
- [LangGraph Plan-and-Execute](https://langchain-ai.github.io/langgraph/tutorials/plan-and-execute/)
