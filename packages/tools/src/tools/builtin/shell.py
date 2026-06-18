"""命令白名单内的 subprocess 工具。"""

from __future__ import annotations

import subprocess
from typing import Any

from common.errors import ToolError
from tools.registry import tool

_DEFAULT_TIMEOUT_S = 30.0


@tool(
    name="shell",
    description=(
        "执行外部命令。每次调用必须传 allowed_commands 白名单,argv[0] 不在白名单内会被拒。"
    ),
    require_approval=True,
    timeout_s=_DEFAULT_TIMEOUT_S,
)
def shell(argv: list[str], allowed_commands: list[str]) -> dict[str, Any]:
    """执行白名单内的命令。

    Args:
        argv: 完整命令行列表,argv[0] 是命令名。
        allowed_commands: 允许的命令名列表(只看 argv[0])。

    Returns:
        dict: {"returncode": int, "stdout": str, "stderr": str}
    """
    if not argv:
        raise ToolError("shell argv is empty", tool_name="shell")

    cmd = argv[0]
    if cmd not in allowed_commands:
        raise ToolError(
            f"shell command {cmd!r} not in allowed_commands {allowed_commands}",
            tool_name="shell",
            context={"command": cmd, "allowed": allowed_commands},
        )

    try:
        proc = subprocess.run(  # noqa: S603 - argv 已校验白名单
            argv,
            capture_output=True,
            text=True,
            timeout=_DEFAULT_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        raise ToolError(
            f"shell command timed out after {_DEFAULT_TIMEOUT_S}s",
            tool_name="shell",
            context={"argv": argv},
        ) from e
    except OSError as e:
        raise ToolError(
            f"shell exec failed: {type(e).__name__}: {e}",
            tool_name="shell",
            context={"argv": argv},
        ) from e

    return {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


__all__ = ["shell"]
