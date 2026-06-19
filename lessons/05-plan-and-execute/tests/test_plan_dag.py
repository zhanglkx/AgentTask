"""plan_dag 测试：DAG 结构验证。"""

from __future__ import annotations

import pytest

from plan_dag import PlanDAG, PlanStep


@pytest.mark.fast
def test_plan_step_creation() -> None:
    """PlanStep 应包含 id / name / dependencies。"""
    step = PlanStep(id="s1", name="调查背景", dependencies=[])
    assert step.id == "s1"
    assert step.name == "调查背景"
    assert step.dependencies == []


@pytest.mark.fast
def test_plan_dag_add_step() -> None:
    """PlanDAG 应能添加步骤。"""
    dag = PlanDAG()
    dag.add_step(PlanStep(id="s1", name="步骤1", dependencies=[]))
    dag.add_step(PlanStep(id="s2", name="步骤2", dependencies=["s1"]))
    assert len(dag.steps) == 2


@pytest.mark.fast
def test_plan_dag_execution_order() -> None:
    """PlanDAG 应返回正确的执行顺序（依赖排序）。"""
    dag = PlanDAG()
    dag.add_step(PlanStep(id="s1", name="调查", dependencies=[]))
    dag.add_step(PlanStep(id="s2", name="分析", dependencies=["s1"]))
    dag.add_step(PlanStep(id="s3", name="总结", dependencies=["s2"]))

    order = dag.execution_order()
    assert order == ["s1", "s2", "s3"]


@pytest.mark.fast
def test_plan_dag_parallel_steps() -> None:
    """无依赖的步骤可并行执行（顺序任意但都在依赖步骤之后）。"""
    dag = PlanDAG()
    dag.add_step(PlanStep(id="s1", name="调查A", dependencies=[]))
    dag.add_step(PlanStep(id="s2", name="调查B", dependencies=[]))
    dag.add_step(PlanStep(id="s3", name="汇总", dependencies=["s1", "s2"]))

    order = dag.execution_order()
    # s3 必在 s1 和 s2 之后
    assert order.index("s3") > order.index("s1")
    assert order.index("s3") > order.index("s2")
