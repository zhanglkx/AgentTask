"""路径白名单内的文件读/写工具。

注: 本文件**故意**不使用 ``from __future__ import annotations``。
原因: ``@tool`` 装饰器内部用 ``inspect.signature(func).parameters[...].annotation``
读取注解,再传给 pydantic ``create_model``。开启 PEP-563 后注解变字符串,pydantic
会把 ``Literal["read", "write"]`` 当 forward ref,在缺少 ``Literal`` 名字解析作用域
的情况下抛 ``PydanticUserError: ... is not fully defined``。让注解保持运行时可解析的实
体即可。
"""

from pathlib import Path
from typing import Literal

from common.errors import ToolError
from tools.registry import tool


def _resolve_within(allowed_root: str, path: str) -> Path:
    """把 path 解析为绝对路径,并校验落在 allowed_root 之内。"""
    root = Path(allowed_root).resolve()
    target = Path(path).resolve()
    try:
        target.relative_to(root)
    except ValueError as e:
        raise ToolError(
            f"path {target} is outside allowed_root {root}",
            tool_name="file_io",
            context={"path": str(target), "allowed_root": str(root)},
        ) from e
    return target


@tool(
    name="file_io",
    description="读/写文件。必须提供 allowed_root,所有操作严格限定在该目录下。",
)
def file_io(
    action: Literal["read", "write"],
    path: str,
    allowed_root: str,
    content: str = "",
) -> str:
    """文件读写。

    Args:
        action: read 或 write。
        path: 目标文件路径(绝对或相对均可,会与 allowed_root 解析比较)。
        allowed_root: 允许操作的根目录(必填)。
        content: 仅在 write 时使用。

    Returns:
        str: read 返回文件内容;write 返回 "ok"。
    """
    if action not in ("read", "write"):
        raise ToolError(
            f"file_io action must be 'read' or 'write', got {action!r}",
            tool_name="file_io",
        )

    target = _resolve_within(allowed_root, path)

    if action == "read":
        try:
            return target.read_text(encoding="utf-8")
        except OSError as e:
            raise ToolError(
                f"file_io read failed: {type(e).__name__}: {e}",
                tool_name="file_io",
                context={"path": str(target)},
            ) from e

    # write
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return "ok"
    except OSError as e:
        raise ToolError(
            f"file_io write failed: {type(e).__name__}: {e}",
            tool_name="file_io",
            context={"path": str(target)},
        ) from e


__all__ = ["file_io"]
