"""用 nbformat 程序化生成 .ipynb notebook。

用法:
    uv run python scripts/create_notebook.py lessons/01-foundations/notebook.ipynb \
        --title "LLM 基础" \
        --cells "cell1.md:markdown" "cell2.py:code"

设计原则:
    - notebook 由脚本生成,不手工编辑(保证 reproducibility)
    - markdown cell 用中文讲解,code cell 用 Python
    - 所有 code cell 使用 fake LLM,不调真实 API
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import nbformat


def create_notebook(
    title: str,
    cells: list[tuple[str, str]],
    output_path: str,
) -> None:
    """创建 notebook 并写入文件。

    Args:
        title: notebook 标题（写在第一个 markdown cell）。
        cells: (content, cell_type) 列表，cell_type 为 "markdown" 或 "code"。
        output_path: 输出 .ipynb 文件路径。
    """
    nb = nbformat.v4.new_notebook()
    nb.cells.append(nbformat.v4.new_markdown_cell(source=f"# {title}\n"))

    for content, cell_type in cells:
        if cell_type == "markdown":
            nb.cells.append(nbformat.v4.new_markdown_cell(source=content))
        elif cell_type == "code":
            nb.cells.append(nbformat.v4.new_code_cell(source=content))
        else:
            print(f"未知 cell 类型: {cell_type}", file=sys.stderr)
            sys.exit(1)

    nbformat.write(nb, output_path)
    print(f"✓ notebook 已生成: {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="程序化生成 .ipynb notebook")
    parser.add_argument("output", help="输出 .ipynb 文件路径")
    parser.add_argument("--title", required=True, help="Notebook 标题")
    parser.add_argument(
        "--cells",
        nargs="*",
        help="cell 列表，格式: 'content:type'（type=markdown/code）",
    )
    args = parser.parse_args()

    parsed_cells: list[tuple[str, str]] = []
    for cell_spec in args.cells or []:
        parts = cell_spec.rsplit(":", 1)
        if len(parts) != 2:
            print(f"cell 格式错误: {cell_spec}（应为 'content:type'）", file=sys.stderr)
            return 1
        parsed_cells.append((parts[0], parts[1]))

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    create_notebook(args.title, parsed_cells, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
