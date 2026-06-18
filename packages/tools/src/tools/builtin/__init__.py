"""内置工具集合。

通过 ``from . import <submodule>`` 显式暴露子模块,以便:
1. ``from tools.builtin.web_search import web_search`` 拿到 Tool 实例(供使用方调用)。
2. ``monkeypatch.setattr("tools.builtin.web_search._get_client", ...)`` 等基于
   dotted path 的解析能拿到模块对象。

如果改用 ``from .web_search import web_search`` re-export Tool 实例,会把
``tools.builtin.web_search`` 这一父包属性从子模块覆盖成 Tool 实例,导致
pytest monkeypatch 的字符串路径解析失败(它走 ``getattr`` 链)。
"""

from __future__ import annotations

from . import file_io, python_repl, shell, web_scrape, web_search

__all__ = ["file_io", "python_repl", "shell", "web_scrape", "web_search"]
