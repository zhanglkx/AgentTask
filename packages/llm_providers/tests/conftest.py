"""llm_providers 测试共用 fixtures。"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """每个测试前清空 AGENTTASK_ 与 LLM provider 相关环境变量。"""
    for key in list(os.environ.keys()):
        if key.startswith(("AGENTTASK_", "OPENAI_", "ANTHROPIC_", "DEEPSEEK_")):
            monkeypatch.delenv(key, raising=False)
    yield
