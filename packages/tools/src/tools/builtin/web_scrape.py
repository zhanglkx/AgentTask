"""trafilatura 网页正文抓取工具。"""

from __future__ import annotations

from typing import Any

import httpx
import trafilatura
from readability import Document  # type: ignore[import-untyped, unused-ignore]

from common.errors import ToolError
from tools.registry import tool

_TIMEOUT_S = 15.0
_USER_AGENT = "AgentTask/0.1 (+https://github.com/zhanglkx/AgentTask)"


@tool(
    name="web_scrape",
    description="抓取指定 URL 的主体正文(自动跳过导航/广告/侧栏)。",
)
def web_scrape(url: str) -> dict[str, Any]:
    """抓取并提取正文。

    Args:
        url: 目标网页 URL(http/https)。

    Returns:
        dict: {"url": str, "content": str, "title": str | None}
    """
    try:
        with httpx.Client(timeout=_TIMEOUT_S, headers={"User-Agent": _USER_AGENT}) as client:
            resp = client.get(url, follow_redirects=True)
    except httpx.HTTPError as e:
        raise ToolError(
            f"web_scrape http error for {url}: {type(e).__name__}: {e}",
            tool_name="web_scrape",
            context={"url": url},
        ) from e

    if resp.status_code >= 400:
        raise ToolError(
            f"web_scrape got HTTP {resp.status_code} for {url}",
            tool_name="web_scrape",
            context={"url": url, "status": resp.status_code},
        )

    extracted = trafilatura.extract(
        resp.text,
        include_comments=False,
        include_tables=True,
        favor_recall=True,
    )
    if not extracted:
        # fallback: 用 readability-lxml
        try:
            doc = Document(resp.text)
            extracted = doc.summary()
        except Exception:
            # 双解析兜底失败时静默吞,返回空 content;调用方据此判断。
            extracted = ""

    title: str | None = None
    try:
        meta = trafilatura.extract_metadata(resp.text)
        if meta is not None:
            title = meta.title
    except Exception:
        title = None  # 元数据提取失败不影响正文返回

    return {"url": url, "content": extracted or "", "title": title}


__all__ = ["web_scrape"]
