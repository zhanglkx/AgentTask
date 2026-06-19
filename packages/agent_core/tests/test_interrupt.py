"""interrupt 包装测试。"""

from __future__ import annotations

from typing import Any

import pytest

from agent_core.interrupt import request_interrupt


@pytest.mark.fast
def test_request_interrupt_calls_langgraph_interrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """request_interrupt 应调用 langgraph.types.interrupt 并透传 payload。"""
    captured: dict[str, Any] = {}

    def fake_interrupt(value: dict[str, Any]) -> str:
        captured.update(value)
        return "resumed-with-foo"

    monkeypatch.setattr("agent_core.interrupt._interrupt", fake_interrupt)

    result = request_interrupt(
        reason="approve_tool_call",
        payload={"tool": "shell", "argv": ["rm", "-rf", "/"]},
    )
    assert result == "resumed-with-foo"
    assert captured["reason"] == "approve_tool_call"
    assert captured["payload"] == {"tool": "shell", "argv": ["rm", "-rf", "/"]}


@pytest.mark.fast
def test_request_interrupt_default_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """payload=None 时应传 {} 给底层。"""
    captured: dict[str, Any] = {}

    def fake_interrupt(value: dict[str, Any]) -> Any:
        captured.update(value)
        return None

    monkeypatch.setattr("agent_core.interrupt._interrupt", fake_interrupt)

    request_interrupt(reason="confirm")
    assert captured["payload"] == {}
