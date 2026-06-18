"""tools: AgentTask 工具层。

公开 API:
- Tool: 抽象基类
- tool: 装饰器(自动注册)
- get_tool / list_tools: 注册表查询
"""

from __future__ import annotations

from .base import Tool
from .registry import get_tool, list_tools, tool

__version__ = "0.1.0"

__all__ = ["Tool", "__version__", "get_tool", "list_tools", "tool"]
