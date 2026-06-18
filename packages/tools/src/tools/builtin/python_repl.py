"""安全简版 Python 表达式求值工具。

M2a 阶段:仅支持算术 + 字面量,通过 AST 白名单实现。
真实代码沙箱(任意函数调用 / import 等)留给 M4 `packages/sandbox`。
"""

from __future__ import annotations

import ast
import operator as op
from typing import Any

from common.errors import ToolError
from tools.registry import tool

_BIN_OPS: dict[type[ast.operator], Any] = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
}

_UNARY_OPS: dict[type[ast.unaryop], Any] = {
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}

_ALLOWED_NODES: tuple[type[ast.AST], ...] = (
    ast.Expression,
    ast.Constant,
    ast.BinOp,
    ast.UnaryOp,
    ast.List,
    ast.Tuple,
    ast.Dict,
    ast.Set,
)


def _eval_node(node: ast.AST) -> Any:  # noqa: PLR0911 - 多 return 是 AST 分派的最清晰写法
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        op_func = _BIN_OPS.get(type(node.op))
        if op_func is None:
            raise ToolError(
                f"binary op {type(node.op).__name__} not allowed",
                tool_name="python_repl",
            )
        return op_func(_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        op_func = _UNARY_OPS.get(type(node.op))
        if op_func is None:
            raise ToolError(
                f"unary op {type(node.op).__name__} not allowed",
                tool_name="python_repl",
            )
        return op_func(_eval_node(node.operand))
    if isinstance(node, ast.List):
        return [_eval_node(e) for e in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(e) for e in node.elts)
    if isinstance(node, ast.Dict):
        return {
            _eval_node(k) if k else None: _eval_node(v)
            for k, v in zip(node.keys, node.values, strict=True)
        }
    if isinstance(node, ast.Set):
        return {_eval_node(e) for e in node.elts}
    raise ToolError(
        f"AST node {type(node).__name__} not allowed in python_repl",
        tool_name="python_repl",
    )


@tool(
    name="python_repl",
    description="求值受限 Python 表达式(仅算术 + list/dict/tuple/set 字面量,无函数调用)。",
    require_approval=True,
)
def python_repl(expression: str) -> Any:
    """求值表达式。

    Args:
        expression: 单行表达式(no statements)。

    Returns:
        Any: 求值结果。
    """
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise ToolError(f"python_repl syntax error: {e}", tool_name="python_repl") from e

    # 先扫一遍所有节点,确保都在白名单内。
    # ast.expr_context 是 List/Dict/Set/Tuple 等容器节点的 ctx 属性类型(eval 模式下都是 Load),
    # 不会真正读取外部变量,允许通过即可。
    allowed_super: tuple[type[ast.AST], ...] = (
        *_ALLOWED_NODES,
        ast.operator,
        ast.unaryop,
        ast.expr_context,
    )
    for sub in ast.walk(tree):
        if not isinstance(sub, allowed_super):
            raise ToolError(
                f"AST node {type(sub).__name__} not allowed in python_repl",
                tool_name="python_repl",
            )
    return _eval_node(tree)


__all__ = ["python_repl"]
