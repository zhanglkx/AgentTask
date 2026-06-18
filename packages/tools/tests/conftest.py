"""packages/tools 测试共用 fixtures。"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """每个测试前清空 AGENTTASK_ 与 TAVILY_ 前缀环境变量。"""
    for key in list(os.environ.keys()):
        if key.startswith(("AGENTTASK_", "TAVILY_")):
            monkeypatch.delenv(key, raising=False)
    yield


@pytest.fixture(autouse=True)
def _clear_registry() -> Iterator[None]:
    """每个测试前后清空 tools 全局注册表,避免互相污染。

    `tools.registry` 在 Task 3 引入,先尝试 import,失败则跳过(Task 1/2 测试不依赖)。
    """
    try:
        from tools import registry as _registry  # type: ignore[attr-defined,unused-ignore]
    except ImportError:
        yield
        return
    _registry._REGISTRY.clear()
    yield
    _registry._REGISTRY.clear()
