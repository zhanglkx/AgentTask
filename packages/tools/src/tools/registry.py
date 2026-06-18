"""@tool 装饰器与全局注册表。

设计:
- 装饰器读函数签名,用 pydantic.create_model 生成 args_schema。
- 同步函数 → _run;async 函数 → _arun(同步 _run 走 LangChain 默认 fallback)。
- 注册表是模块级 dict;测试 fixture 在每个测试前后清空。
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, create_model

from common.errors import ConfigError

from .base import Tool

_REGISTRY: dict[str, Tool] = {}


def _build_args_schema(func: Callable[..., Any], schema_name: str) -> type[BaseModel]:
    """从函数签名生成 pydantic args_schema。

    跳过 self / cls / *args / **kwargs。无 default 的字段标 required。
    """
    sig = inspect.signature(func)
    fields: dict[str, Any] = {}
    for pname, param in sig.parameters.items():
        if pname in {"self", "cls"}:
            continue
        if param.kind in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}:
            continue
        annotation = param.annotation if param.annotation is not inspect.Parameter.empty else Any
        default = param.default if param.default is not inspect.Parameter.empty else ...
        fields[pname] = (annotation, default)
    return create_model(schema_name, **fields)  # type: ignore[call-overload,no-any-return,unused-ignore]


def tool(
    *,
    name: str,
    description: str,
    require_approval: bool = False,
    timeout_s: float | None = None,
) -> Callable[[Callable[..., Any]], Tool]:
    """把函数注册为工具,返回 Tool 实例(替代原函数)。

    Args:
        name: 工具名(全局唯一)。
        description: 描述,会传给 LLM 做 tool selection。
        require_approval: 高危工具,M4 HITL 会拦截。
        timeout_s: 超时秒数,M4 sandbox 用。

    Raises:
        ConfigError: 重名注册。
    """

    # 用别名捕获闭包变量;类体作用域不是闭包,无法直接引用与类属性同名的外层名。
    _tool_name = name
    _tool_description = description
    _tool_require_approval = require_approval
    _tool_timeout_s = timeout_s

    def decorator(func: Callable[..., Any]) -> Tool:
        if _tool_name in _REGISTRY:
            raise ConfigError(
                f"tool name {_tool_name!r} already registered "
                f"(existing: {_REGISTRY[_tool_name]!r})",
                context={"name": _tool_name},
            )

        schema_cls = _build_args_schema(func, schema_name=f"{_tool_name}__Args")
        is_async = asyncio.iscoroutinefunction(func)

        class _DecoratedTool(Tool):
            # 显式声明类型,避免 mypy 把基类字段视为 ClassVar
            name: str = _tool_name  # type: ignore[assignment,unused-ignore]
            description: str = _tool_description  # type: ignore[assignment,unused-ignore]
            args_schema: type[BaseModel] = schema_cls  # type: ignore[assignment,unused-ignore]
            require_approval: bool = _tool_require_approval
            timeout_s: float | None = _tool_timeout_s

            def _run(self, **kwargs: Any) -> Any:
                if is_async:
                    return asyncio.run(func(**kwargs))
                return func(**kwargs)

            async def _arun(self, **kwargs: Any) -> Any:
                if is_async:
                    return await func(**kwargs)
                return func(**kwargs)

        instance = _DecoratedTool()
        _REGISTRY[_tool_name] = instance
        return instance

    return decorator


def get_tool(name: str) -> Tool:
    """按名查工具。未注册抛 ConfigError。"""
    if name not in _REGISTRY:
        raise ConfigError(
            f"tool not registered: {name!r}; known: {sorted(_REGISTRY)}",
            context={"name": name},
        )
    return _REGISTRY[name]


def list_tools() -> list[Tool]:
    """返回所有已注册工具(顺序 = 注册顺序)。"""
    return list(_REGISTRY.values())


__all__ = ["get_tool", "list_tools", "tool"]
