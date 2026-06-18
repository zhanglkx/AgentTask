"""Tool 抽象基类。

继承 langchain_core BaseTool 让 LangGraph 直接消费;同时统一错误处理与
仓库特有元数据(require_approval / timeout_s)。
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool
from pydantic import ValidationError

from common.errors import ToolError


class Tool(BaseTool):
    """所有仓库工具的统一基类。

    子类必须定义:
    - name: str
    - description: str
    - args_schema: type[BaseModel]
    - _run(self, **kwargs) -> Any  (同步实现)

    可选 override:
    - _arun(self, **kwargs) -> Any  (async 实现,不 override 时 LangChain 会调同步版本)

    仓库特有元数据(LangChain BaseTool 没有,此处扩展):
    - require_approval: bool —— M4 HITL 高危工具审批门;M2a 默认 False。
    - timeout_s: float | None —— M4 sandbox 超时;M2a 默认 None。
    """

    require_approval: bool = False
    timeout_s: float | None = None

    def run(  # type: ignore[override,unused-ignore]
        self,
        tool_input: str | dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """同步执行入口。捕获所有异常 → 包装为 ToolError。"""
        try:
            return super().run(tool_input, *args, **kwargs)
        except ValidationError as e:
            raise ToolError(
                f"input validation failed for tool {self.name!r}: {e}",
                tool_name=self.name,
                context={"errors": e.errors()},
            ) from e
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(
                f"tool {self.name!r} raised {type(e).__name__}: {e}",
                tool_name=self.name,
            ) from e

    async def arun(  # type: ignore[override,unused-ignore]
        self,
        tool_input: str | dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """异步执行入口。捕获所有异常 → 包装为 ToolError。"""
        try:
            return await super().arun(tool_input, *args, **kwargs)
        except ValidationError as e:
            raise ToolError(
                f"input validation failed for tool {self.name!r}: {e}",
                tool_name=self.name,
                context={"errors": e.errors()},
            ) from e
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(
                f"tool {self.name!r} raised {type(e).__name__}: {e}",
                tool_name=self.name,
            ) from e


__all__ = ["Tool"]
