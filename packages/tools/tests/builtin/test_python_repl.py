"""python_repl 工具测试(M2a 安全简版)。"""

from __future__ import annotations

import pytest

from common.errors import ToolError
from tools.builtin.python_repl import python_repl


@pytest.mark.fast
def test_python_repl_arithmetic() -> None:
    """支持基本算术表达式。"""
    assert python_repl.run({"expression": "1 + 2 * 3"}) == 7
    assert python_repl.run({"expression": "(10 - 4) / 2"}) == 3.0


@pytest.mark.fast
def test_python_repl_literals() -> None:
    """支持 list / dict / str / 数字字面量。"""
    assert python_repl.run({"expression": "[1, 2, 3]"}) == [1, 2, 3]
    assert python_repl.run({"expression": "{'a': 1}"}) == {"a": 1}
    assert python_repl.run({"expression": "'hello'"}) == "hello"


@pytest.mark.fast
def test_python_repl_blocks_function_call() -> None:
    """禁止函数调用(避免任意代码执行)。"""
    with pytest.raises(ToolError, match="not allowed"):
        python_repl.run({"expression": "__import__('os').system('rm -rf /')"})


@pytest.mark.fast
def test_python_repl_blocks_attribute_access() -> None:
    """禁止属性访问(防止 ()._dunder 越权)。"""
    with pytest.raises(ToolError, match="not allowed"):
        python_repl.run({"expression": "(1).__class__"})


@pytest.mark.fast
def test_python_repl_marks_require_approval() -> None:
    """python_repl 默认应标 require_approval=True。"""
    assert python_repl.require_approval is True


@pytest.mark.fast
def test_python_repl_syntax_error_raises_toolerror() -> None:
    """语法错误应抛 ToolError。"""
    with pytest.raises(ToolError, match="python_repl"):
        python_repl.run({"expression": "1 +"})


@pytest.mark.fast
def test_python_repl_unary_and_containers() -> None:
    """覆盖 UnaryOp / Tuple / Set 字面量分支(都是文档承诺支持的字面量)。"""
    assert python_repl.run({"expression": "-5"}) == -5
    assert python_repl.run({"expression": "+3"}) == 3
    assert python_repl.run({"expression": "(1, 2, 3)"}) == (1, 2, 3)
    assert python_repl.run({"expression": "{1, 2, 2, 3}"}) == {1, 2, 3}
