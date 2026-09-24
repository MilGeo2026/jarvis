"""Rechner-Tool mit sicherer Auswertung (kein eval())."""
from __future__ import annotations

import ast
import operator
from typing import Any

from tools.base import Tool, ToolResult

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class CalculationError(Exception):
    pass


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.operand))
    raise CalculationError("Ungueltiger Ausdruck.")


def safe_eval(expression: str) -> float:
    try:
        tree = ast.parse(expression, mode="eval")
        return _eval_node(tree.body)
    except (SyntaxError, CalculationError, ZeroDivisionError, TypeError) as exc:
        raise CalculationError(str(exc)) from exc


def _format_number(value: float) -> str:
    if value == int(value):
        return f"{int(value):,}".replace(",", ".")
    text = f"{value:,.4f}".rstrip("0").rstrip(".")
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


class CalculatorTool(Tool):
    name = "calculator"
    description = "Berechnet einen mathematischen Ausdruck, z. B. '245 * 37' oder '(12 + 8) / 4'."
    parameters = {
        "type": "object",
        "properties": {"expression": {"type": "string", "description": "Mathematischer Ausdruck"}},
        "required": ["expression"],
    }

    def execute(self, arguments: dict[str, Any]) -> ToolResult:
        expression = str(arguments.get("expression", "")).strip()
        if not expression:
            return ToolResult(success=False, message="Es wurde kein Ausdruck angegeben.")
        try:
            result = safe_eval(expression)
        except CalculationError:
            return ToolResult(success=False, message=f"Der Ausdruck '{expression}' konnte nicht berechnet werden.")
        return ToolResult(success=True, message=f"Das Ergebnis ist {_format_number(result)}.", data={"result": result})
