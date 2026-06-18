"""结构化日志。

设计:
- structlog 输出 JSON 行,适配 ELK / Loki / CloudWatch。
- timestamp / level / event / logger 由 processor 自动注入。
- bind_context 是 contextmanager,用 contextvars 实现跨异步任务安全。
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from typing import IO, Any

import structlog

_VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def configure_logging(
    *,
    level: str = "INFO",
    stream: IO[str] | None = None,
) -> None:
    """配置 stdlib + structlog,输出 JSON 行到 stream（默认 stderr）。

    可重复调用（测试场景）,后调用覆盖前调用。

    Args:
        level: 日志级别字符串,大小写无关,必须在 DEBUG/INFO/WARNING/ERROR/CRITICAL。
        stream: 输出流,None 时用 sys.stderr。
    """
    upper = level.upper()
    if upper not in _VALID_LEVELS:
        raise ValueError(f"invalid log level: {level!r}; expected one of {sorted(_VALID_LEVELS)}")

    target = stream if stream is not None else sys.stderr
    numeric_level = getattr(logging, upper)

    handler = logging.StreamHandler(target)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root = logging.getLogger()
    root.handlers = [h for h in root.handlers if not getattr(h, "_agenttask", False)]
    handler._agenttask = True  # type: ignore[attr-defined]
    root.addHandler(handler)
    root.setLevel(numeric_level)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """返回 structlog BoundLogger（≈ pino 的 logger 子实例）。

    bind() 强制 lazy proxy 立即物化为真正的 BoundLogger,
    避免 isinstance 检查与延迟初始化语义混淆。
    """
    return structlog.get_logger(name).bind()  # type: ignore[no-any-return]


@contextmanager
def bind_context(**kwargs: Any) -> Iterator[None]:
    """在上下文中绑定字段,内部所有日志自动携带。

    用法:
        with bind_context(agent_name="researcher", trace_id="abc"):
            log.info("step")  # 自动带上 agent_name / trace_id
    """
    tokens = structlog.contextvars.bind_contextvars(**kwargs)
    try:
        yield
    finally:
        structlog.contextvars.reset_contextvars(**tokens)


__all__ = ["bind_context", "configure_logging", "get_logger"]
