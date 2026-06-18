"""packages/common 测试共用 fixtures。"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """每个测试开始前清空 AGENTTASK_ 前缀的环境变量,避免外部 .env 干扰。

    autouse=True 表示所有测试自动应用。
    """
    for key in list(os.environ.keys()):
        if key.startswith("AGENTTASK_"):
            monkeypatch.delenv(key, raising=False)
    yield
