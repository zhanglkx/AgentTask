"""第 4 章 conftest：将 src/ 加入 sys.path + 清除工具注册表。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "tests"))


@pytest.fixture(autouse=True)
def _clear_registry() -> None:
    """清除全局工具注册表以避免跨测试污染。"""
    from tools import registry as _reg

    _reg._REGISTRY.clear()
