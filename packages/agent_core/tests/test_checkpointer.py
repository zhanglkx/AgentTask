"""checkpointer 工厂测试。"""

from __future__ import annotations

import pytest
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from agent_core.checkpointer import get_checkpointer


@pytest.mark.fast
def test_dev_returns_memory_saver() -> None:
    """env=dev 应返回 MemorySaver。"""
    cp = get_checkpointer(env="dev")
    assert isinstance(cp, MemorySaver)
    assert isinstance(cp, BaseCheckpointSaver)


@pytest.mark.fast
def test_default_uses_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """env=None 应读 Settings.app_env(默认 dev)。"""
    cp = get_checkpointer()
    assert isinstance(cp, MemorySaver)


@pytest.mark.fast
def test_prod_raises_not_implemented() -> None:
    """env=prod 在 M2a 应抛 NotImplementedError(M3 才接 Postgres)。"""
    with pytest.raises(NotImplementedError, match="M3"):
        get_checkpointer(env="prod")


@pytest.mark.fast
def test_staging_raises_not_implemented() -> None:
    """env=staging 同理。"""
    with pytest.raises(NotImplementedError, match="M3"):
        get_checkpointer(env="staging")


@pytest.mark.fast
def test_unknown_env_raises_config_error() -> None:
    """非法 env 字符串应抛 ConfigError。"""
    from common.errors import ConfigError

    with pytest.raises(ConfigError, match="env"):
        get_checkpointer(env="not-real-env")
