"""LangGraph checkpointer 工厂。

M2a: 仅 dev 环境(MemorySaver)。
M3: 接 PostgresSaver(staging / prod)。
"""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from common.config import AppEnv, get_settings
from common.errors import ConfigError


def get_checkpointer(*, env: str | None = None) -> BaseCheckpointSaver[Any]:
    """构造 checkpointer。

    Args:
        env: 显式指定环境(dev / staging / prod)。None 时读 Settings.app_env。

    Raises:
        ConfigError: env 不是合法 AppEnv。
        NotImplementedError: M2a 阶段 staging / prod 还没接 Postgres。
    """
    if env is None:
        env = get_settings(reload=True).app_env.value
    try:
        chosen = AppEnv(env)
    except ValueError as e:
        raise ConfigError(
            f"unknown env {env!r}; expected one of {[e.value for e in AppEnv]}",
            context={"env": env},
        ) from e

    if chosen is AppEnv.DEV:
        return MemorySaver()

    raise NotImplementedError(
        f"checkpointer for env={chosen.value!r} not yet implemented "
        "(PostgresSaver will be added in M3)"
    )


__all__ = ["get_checkpointer"]
