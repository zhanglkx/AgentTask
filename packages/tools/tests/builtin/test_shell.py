"""shell 工具测试。"""

from __future__ import annotations

import pytest

from common.errors import ToolError
from tools.builtin.shell import shell


@pytest.mark.fast
def test_shell_runs_whitelisted_command() -> None:
    """白名单内的命令应正常执行并返回 stdout。"""
    out = shell.run({"argv": ["echo", "hello"], "allowed_commands": ["echo"]})
    assert out["returncode"] == 0
    assert "hello" in out["stdout"]


@pytest.mark.fast
def test_shell_rejects_non_whitelisted_command() -> None:
    """白名单外的命令应抛 ToolError。"""
    with pytest.raises(ToolError, match="not in allowed_commands"):
        shell.run({"argv": ["rm", "-rf", "/"], "allowed_commands": ["echo", "ls"]})


@pytest.mark.fast
def test_shell_returns_nonzero_on_failure() -> None:
    """失败的命令(returncode != 0)不抛错,但在结果里体现。"""
    out = shell.run({"argv": ["false"], "allowed_commands": ["false"]})
    assert out["returncode"] != 0


@pytest.mark.fast
def test_shell_marks_require_approval() -> None:
    """shell 默认应标 require_approval=True。"""
    assert shell.require_approval is True


@pytest.mark.fast
def test_shell_empty_argv_raises() -> None:
    """空 argv 应抛 ToolError。"""
    with pytest.raises(ToolError, match="argv"):
        shell.run({"argv": [], "allowed_commands": ["echo"]})


@pytest.mark.fast
def test_shell_missing_executable_raises_toolerror() -> None:
    """命令在白名单内但磁盘不存在时,subprocess 抛 OSError 应被包装为 ToolError。"""
    fake = "agenttask_definitely_missing_binary_xyz"
    with pytest.raises(ToolError, match="shell"):
        shell.run({"argv": [fake], "allowed_commands": [fake]})
