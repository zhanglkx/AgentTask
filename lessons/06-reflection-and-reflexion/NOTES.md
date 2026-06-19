# 第 6 章小结

## 核心概念

1. **Basic Reflection**：generator → critic → 决定（ACCEPT 或继续修订）
2. **Reflexion**：Reflection + episodic memory——从过去的成功/失败中学习
3. **ExperienceStore**：存储与召回经验，类似 Git log 或笔记系统
4. **Success marker**：critic 判断当前输出足够好（如 "SUCCESS"），停止循环
5. **准确率基线**：对比 Reflection / Reflexion / 无反思三者的输出质量

## 进阶阅读

- [Reflexion 论文](https://arxiv.org/abs/2303.11366)
- [LangGraph Reflection](https://langchain-ai.github.io/langgraph/tutorials/reflection/)
