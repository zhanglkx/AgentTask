"""Plan DAG：计划的有向无环图表示。

类比前端:
    - PlanStep ≈ Task item（id + name + deps）
    - PlanDAG ≈ Dependency graph（像 React 的 useEffect deps）
    - execution_order() ≈ Topological sort（确保依赖顺序）

核心用途:
    研究类任务的 plan 不是简单线性列表，
    有些步骤可并行执行（无依赖），有些必须等前置完成。
    DAG 让 executor 可以并行处理独立步骤。
"""

from __future__ import annotations

from pydantic import BaseModel


class PlanStep(BaseModel):
    """单个计划步骤。"""

    id: str
    name: str
    dependencies: list[str] = []


class PlanDAG:
    """计划的有向无环图。"""

    def __init__(self) -> None:
        self.steps: dict[str, PlanStep] = {}

    def add_step(self, step: PlanStep) -> None:
        """添加步骤到 DAG。"""
        self.steps[step.id] = step

    def execution_order(self) -> list[str]:
        """返回拓扑排序的执行顺序（依赖步骤先执行）。

        使用 Kahn's algorithm（BFS 拓扑排序）。
        """
        in_degree: dict[str, int] = {s.id: len(s.dependencies) for s in self.steps.values()}
        queue: list[str] = [s_id for s_id, deg in in_degree.items() if deg == 0]
        order: list[str] = []

        while queue:
            current = queue.pop(0)
            order.append(current)
            # 减少依赖 current 的所有步骤的入度
            for step in self.steps.values():
                if current in step.dependencies:
                    in_degree[step.id] -= 1
                    if in_degree[step.id] == 0:
                        queue.append(step.id)

        return order
