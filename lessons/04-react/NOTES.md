# 第 4 章小结

## 核心概念

1. **ReAct**：Reasoning（思考）+ Acting（行动）交替循环，直到得出最终答案
2. **StateGraph**：LangGraph 的核心——有向图 + 共享 state，每个 node 是 `(state) -> partial_state_update`
3. **add_messages reducer**：合并新旧消息列表，是 LangGraph state 的核心机制
4. **条件边**：根据 state（如是否有 tool_calls）决定下一步走哪条边
5. **手写 vs prebuilt**：手写看清底层，prebuilt 提供生产级封装——两者等价

## 进阶阅读

- [ReAct 论文](https://arxiv.org/abs/2210.03629)
- [LangGraph 官方教程](https://langchain-ai.github.io/langgraph/)
- [LangGraph ReAct Agent](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent/)
