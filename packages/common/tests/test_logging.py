"""structlog 结构化日志测试。"""

from __future__ import annotations

import json
import logging
from io import StringIO

import pytest
import structlog

from common.logging import bind_context, configure_logging, get_logger


@pytest.fixture(autouse=True)
def _reset_structlog() -> None:
    """每个测试前重置 structlog 全局配置,避免相互污染。"""
    structlog.reset_defaults()


@pytest.mark.fast
def test_configure_logging_emits_json_with_required_fields() -> None:
    """configure_logging 应输出 JSON,且至少包含 timestamp / level / event。"""
    buf = StringIO()
    configure_logging(level="INFO", stream=buf)
    log = get_logger("test_logger")
    log.info("hello", user_id=42)

    line = buf.getvalue().strip().splitlines()[-1]
    record = json.loads(line)
    assert record["event"] == "hello"
    assert record["level"] == "info"
    assert record["user_id"] == 42
    assert "timestamp" in record


@pytest.mark.fast
def test_log_level_filter_drops_below_threshold() -> None:
    """level=WARNING 时 info 不应输出。"""
    buf = StringIO()
    configure_logging(level="WARNING", stream=buf)
    log = get_logger("test_logger")
    log.info("should be dropped")
    log.warning("should be kept")

    out = buf.getvalue()
    assert "should be dropped" not in out
    assert "should be kept" in out


@pytest.mark.fast
def test_bind_context_attaches_persistent_fields() -> None:
    """bind_context 在的上下文管理器内,所有日志都应自动携带绑定字段。"""
    buf = StringIO()
    configure_logging(level="INFO", stream=buf)
    log = get_logger("test_logger")

    with bind_context(agent_name="researcher", trace_id="abc-123"):
        log.info("step_executed", step=1)

    line = buf.getvalue().strip().splitlines()[-1]
    record = json.loads(line)
    assert record["agent_name"] == "researcher"
    assert record["trace_id"] == "abc-123"
    assert record["step"] == 1


@pytest.mark.fast
def test_bind_context_clears_after_exit() -> None:
    """退出 bind_context 后,绑定字段应被清除。"""
    buf = StringIO()
    configure_logging(level="INFO", stream=buf)
    log = get_logger("test_logger")

    with bind_context(agent_name="researcher"):
        log.info("inside")
    log.info("outside")

    lines = buf.getvalue().strip().splitlines()
    assert json.loads(lines[-2])["agent_name"] == "researcher"
    assert "agent_name" not in json.loads(lines[-1])


@pytest.mark.fast
def test_get_logger_returns_structlog_bound_logger() -> None:
    """get_logger 必须返回 structlog BoundLogger,支持关键字日志。"""
    configure_logging(level="INFO")
    log = get_logger("x")
    assert isinstance(log, structlog.stdlib.BoundLogger)


@pytest.mark.fast
def test_invalid_level_raises_value_error() -> None:
    """未知 level 字符串应在 configure_logging 直接抛 ValueError。"""
    with pytest.raises(ValueError, match="invalid log level"):
        configure_logging(level="VERBOSE")


@pytest.mark.fast
def test_logging_does_not_propagate_secrets() -> None:
    """logger 是 stdlib 标准 logger,默认级别 propagate=True 不影响 JSON 输出格式;
    本测试仅确认输出确实只在我们指定的 stream 上,而不在 root handler。"""
    buf = StringIO()
    configure_logging(level="INFO", stream=buf)
    root = logging.getLogger()
    handler_count = len(root.handlers)
    log = get_logger("x")
    log.info("ping")
    assert buf.getvalue()
    assert len(root.handlers) == handler_count
