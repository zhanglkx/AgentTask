"""仓库级 smoke test。

确保 M0 阶段的基础设施（pyproject 解析、uv workspace、目录结构）正常。
后续里程碑会在各 package / app 内部添加各自的 tests/。
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.fast
def test_pyproject_toml_is_valid() -> None:
    """根 pyproject.toml 必须可解析且声明了 uv workspace。"""
    pyproject = REPO_ROOT / "pyproject.toml"
    assert pyproject.exists(), "缺少根 pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert data["project"]["name"] == "agent-task"
    assert data["project"]["requires-python"].startswith(">=3.12")
    assert data["tool"]["uv"]["workspace"]["members"] == ["packages/*", "apps/*"]


@pytest.mark.fast
def test_required_top_level_files_exist() -> None:
    """M0 必须产出的顶层文件都存在。"""
    required = [
        ".python-version",
        ".gitignore",
        ".dockerignore",
        ".env.example",
        "ruff.toml",
        "mypy.ini",
        ".pre-commit-config.yaml",
        "Makefile",
        "docker-compose.yml",
        "LICENSE",
        "README.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        ".editorconfig",
        "mkdocs.yml",
    ]
    missing = [name for name in required if not (REPO_ROOT / name).exists()]
    assert not missing, f"缺少文件: {missing}"


@pytest.mark.fast
def test_required_directories_exist() -> None:
    """M0 必须产出的目录骨架都存在。"""
    required_dirs = [
        "packages",
        "apps",
        "lessons",
        "examples",
        "scripts",
        "docs",
        "docs/concepts",
        "docs/prerequisites",
        ".vscode",
        ".devcontainer",
        ".github/workflows",
    ]
    missing = [name for name in required_dirs if not (REPO_ROOT / name).is_dir()]
    assert not missing, f"缺少目录: {missing}"


@pytest.mark.fast
def test_python_version_pinned_to_312() -> None:
    """`.python-version` 必须固定到 3.12。"""
    content = (REPO_ROOT / ".python-version").read_text(encoding="utf-8").strip()
    assert content == "3.12", f"期望 3.12,实际 {content!r}"


@pytest.mark.fast
def test_prerequisites_doc_exists_and_nonempty() -> None:
    """Python 速查文档必须存在且非空。"""
    doc = REPO_ROOT / "docs" / "prerequisites" / "python-for-js-devs.md"
    assert doc.exists(), "缺少 Python 速查文档"
    assert doc.stat().st_size > 1000, "速查文档过短,可能未完整产出"


@pytest.mark.fast
def test_init_db_script_importable() -> None:
    """init_db 脚本必须可 import 不报错（M0 阶段为占位）。"""
    import importlib.util

    script_path = REPO_ROOT / "scripts" / "init_db.py"
    assert script_path.exists(), "缺少 scripts/init_db.py"
    spec = importlib.util.spec_from_file_location("init_db", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "main"), "init_db.py 必须导出 main()"
