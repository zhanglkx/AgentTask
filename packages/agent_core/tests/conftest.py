"""packages/agent_core 测试共用 fixtures。"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """每个测试前清空 AGENTTASK_ 前缀环境变量。"""
    for key in list(os.environ.keys()):
        if key.startswith(("AGENTTASK_", "OPENAI_", "ANTHROPIC_", "DEEPSEEK_")):
            monkeypatch.delenv(key, raising=False)
    yield


@pytest.fixture(autouse=True)
def _clear_tool_registry() -> Iterator[None]:
    """每个测试前后清空 tools 全局注册表(agent_core 测试会注册 fake 工具)。"""
    from tools import registry as _registry

    _registry._REGISTRY.clear()
    yield
    _registry._REGISTRY.clear()
