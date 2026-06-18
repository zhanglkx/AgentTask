"""web_search 工具测试(用 mock,不发真请求)。"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from common.errors import ConfigError, ToolError
from tools.builtin.web_search import web_search


@pytest.mark.fast
def test_web_search_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """无 TAVILY_API_KEY 应抛 ConfigError。"""
    with pytest.raises((ConfigError, ToolError), match="TAVILY"):
        web_search.run({"query": "hello"})


@pytest.mark.fast
def test_web_search_returns_normalized_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """成功返回 list[dict]:title / url / content / score。"""
    monkeypatch.setenv("AGENTTASK_TAVILY_API_KEY", "tvly-test")  # pragma: allowlist secret

    fake_client = MagicMock()
    fake_client.search.return_value = {
        "results": [
            {"title": "Doc A", "url": "https://a.com", "content": "snippet a", "score": 0.9},
            {"title": "Doc B", "url": "https://b.com", "content": "snippet b", "score": 0.7},
        ]
    }

    def fake_factory(*_: Any, **__: Any) -> MagicMock:
        return fake_client

    monkeypatch.setattr("tools.builtin.web_search._get_client", fake_factory)

    out = web_search.run({"query": "anything", "max_results": 2})
    assert isinstance(out, list)
    assert len(out) == 2
    assert out[0]["title"] == "Doc A"
    assert out[0]["url"] == "https://a.com"
    assert out[0]["score"] == 0.9


@pytest.mark.fast
def test_web_search_max_results_passed_to_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """max_results 应透传给 tavily client.search。"""
    monkeypatch.setenv("AGENTTASK_TAVILY_API_KEY", "tvly-test")  # pragma: allowlist secret

    fake_client = MagicMock()
    fake_client.search.return_value = {"results": []}
    monkeypatch.setattr("tools.builtin.web_search._get_client", lambda: fake_client)

    web_search.run({"query": "x", "max_results": 7})
    args, kwargs = fake_client.search.call_args
    assert kwargs.get("max_results") == 7 or (len(args) >= 2 and args[1] == 7)
