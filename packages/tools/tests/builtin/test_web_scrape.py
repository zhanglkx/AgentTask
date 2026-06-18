"""web_scrape 工具测试(用 respx mock httpx)。"""
# pre-commit 的 mypy hook 未列 respx 为 additional_dependencies,直接 import 会报
# import-not-found,而 @respx.mock 装饰器随之被视为 untyped(misc)。这里在测试
# 文件级别禁用这两类错误码,使 hook 与本地 venv mypy 行为一致。
# mypy: disable-error-code="import-not-found,misc"

from __future__ import annotations

import httpx
import pytest
import respx

from common.errors import ToolError
from tools.builtin.web_scrape import web_scrape

_HTML_PAGE = """
<html>
  <head><title>测试页</title></head>
  <body>
    <article>
      <h1>主标题</h1>
      <p>这是一段比较长的正文,长度足够 trafilatura 提取出来。</p>
      <p>第二段正文,带 <a href=\"/x\">内部链接</a>。</p>
    </article>
    <nav>跳过的导航</nav>
  </body>
</html>
""".strip()


@pytest.mark.fast
@respx.mock
def test_web_scrape_extracts_main_content() -> None:
    """trafilatura 应提取 <article> 内的正文,跳过导航。"""
    respx.get("https://example.com/x").mock(return_value=httpx.Response(200, text=_HTML_PAGE))
    out = web_scrape.run({"url": "https://example.com/x"})
    assert isinstance(out, dict)
    assert "主标题" in out["content"] or "正文" in out["content"]
    assert out["url"] == "https://example.com/x"


@pytest.mark.fast
@respx.mock
def test_web_scrape_404_raises_toolerror() -> None:
    """非 2xx 状态应抛 ToolError(tool_name=web_scrape)。"""
    respx.get("https://example.com/missing").mock(
        return_value=httpx.Response(404, text="not found")
    )
    with pytest.raises(ToolError) as exc_info:
        web_scrape.run({"url": "https://example.com/missing"})
    assert exc_info.value.tool_name == "web_scrape"
    assert "404" in str(exc_info.value)


@pytest.mark.fast
@respx.mock
def test_web_scrape_timeout_raises_toolerror() -> None:
    """httpx 超时应包装为 ToolError。"""
    respx.get("https://slow.example.com").mock(side_effect=httpx.TimeoutException)
    with pytest.raises(ToolError, match="web_scrape"):
        web_scrape.run({"url": "https://slow.example.com"})
