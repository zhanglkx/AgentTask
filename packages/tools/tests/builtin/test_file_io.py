"""file_io 工具测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from common.errors import ToolError
from tools.builtin.file_io import file_io


@pytest.mark.fast
def test_file_io_read_within_root(tmp_path: Path) -> None:
    """读取 allowed_root 下的文件应成功。"""
    f = tmp_path / "hello.txt"
    f.write_text("世界", encoding="utf-8")

    out = file_io.run({"action": "read", "path": str(f), "allowed_root": str(tmp_path)})
    assert out == "世界"


@pytest.mark.fast
def test_file_io_write_within_root(tmp_path: Path) -> None:
    """写入 allowed_root 下的文件应成功。"""
    f = tmp_path / "out.txt"
    file_io.run({"action": "write", "path": str(f), "allowed_root": str(tmp_path), "content": "hi"})
    assert f.read_text(encoding="utf-8") == "hi"


@pytest.mark.fast
def test_file_io_path_escape_raises(tmp_path: Path) -> None:
    """越出 allowed_root 应抛 ToolError。"""
    outside = tmp_path.parent / "secret.txt"
    with pytest.raises(ToolError, match="outside allowed_root"):
        file_io.run({"action": "read", "path": str(outside), "allowed_root": str(tmp_path)})


@pytest.mark.fast
def test_file_io_unknown_action_raises(tmp_path: Path) -> None:
    """非 read/write 的 action 应抛 ToolError。"""
    with pytest.raises(ToolError, match="action"):
        file_io.run(
            {"action": "delete", "path": str(tmp_path / "x"), "allowed_root": str(tmp_path)}
        )


@pytest.mark.fast
def test_file_io_read_missing_file_raises(tmp_path: Path) -> None:
    """读不存在文件应抛 ToolError。"""
    with pytest.raises(ToolError, match="file_io"):
        file_io.run(
            {"action": "read", "path": str(tmp_path / "nope.txt"), "allowed_root": str(tmp_path)}
        )


@pytest.mark.fast
def test_file_io_write_oserror_wrapped(tmp_path: Path) -> None:
    """父路径不是目录(已是文件)时 write 应抛 ToolError。"""
    parent = tmp_path / "blocker"
    parent.write_text("i am a file", encoding="utf-8")  # parent 不是目录
    target = parent / "child.txt"
    with pytest.raises(ToolError, match="file_io write failed"):
        file_io.run(
            {
                "action": "write",
                "path": str(target),
                "allowed_root": str(tmp_path),
                "content": "x",
            }
        )
