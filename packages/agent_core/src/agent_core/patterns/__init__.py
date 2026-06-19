"""模式模板集合。"""

from __future__ import annotations

from .plan_execute import build_plan_execute_graph
from .react import build_react_graph

__all__ = ["build_plan_execute_graph", "build_react_graph"]
