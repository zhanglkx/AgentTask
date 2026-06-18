"""Tavily 网页搜索工具。"""

from __future__ import annotations

from typing import Any

from tavily import TavilyClient

from common.config import get_settings
from common.errors import ConfigError
from tools.registry import tool


def _get_client() -> Any:
    """构造 tavily client(单独函数以便测试 mock)。"""
    settings = get_settings(reload=True)
    if settings.tavily_api_key is None:
        raise ConfigError(
            "missing AGENTTASK_TAVILY_API_KEY",
            context={"tool": "web_search"},
        )
    return TavilyClient(api_key=settings.tavily_api_key.get_secret_value())


@tool(
    name="web_search",
    description="用 Tavily 搜索网络,返回排序后的相关网页列表(title/url/content/score)。",
)
def web_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """搜索网络。

    Args:
        query: 搜索关键词或自然语言问题。
        max_results: 返回结果数,1-10。

    Returns:
        list[dict]: 每项含 title / url / content / score。
    """
    client = _get_client()
    raw = client.search(query, max_results=max_results)
    results: list[dict[str, Any]] = raw.get("results", [])
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": float(r.get("score", 0.0)),
        }
        for r in results
    ]


__all__ = ["web_search"]
