from __future__ import annotations

import ast
from decimal import Decimal

from app.core.config import Settings
from app.models.enums import FindingCategory, FindingSeverity
from app.services.static_analysis.types import AnalysisFile, NormalizedFinding

SQL_WORDS = ("select ", "insert ", "update ", "delete ", "where ", " from ")
VALIDATORS = {"isinstance", "int", "str", "float", "bool", "len", "uuid", "UUID"}


def _names(node: ast.AST) -> set[str]:
    return {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}


def _has_raise_or_return(node: ast.AST) -> bool:
    return any(isinstance(child, (ast.Raise, ast.Return)) for child in ast.walk(node))


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _is_validation_call(node: ast.Call) -> bool:
    name = _call_name(node)
    return name in VALIDATORS or name.lower() in VALIDATORS


def _sql_literal(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            lowered = child.value.lower()
            if any(word in lowered for word in SQL_WORDS):
                return True
    return False


def _expression_uses_param_in_string(node: ast.AST, params: set[str]) -> set[str]:
    used = _names(node) & params
    if not used:
        return set()
    if isinstance(node, ast.JoinedStr):
        return used if _sql_literal(node) else set()
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mod, ast.Add)):
        return used if _sql_literal(node) else set()
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "format":
        return used if _sql_literal(node.func.value) else set()
    return set()


class ValidationVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, settings: Settings) -> None:
        self.file_path = file_path
        self.settings = settings
        self.findings: list[NormalizedFinding] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        params = {arg.arg for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs}
        params.discard("self")
        params.discard("cls")
        if not params:
            return
        validated: set[str] = set()
        sql_vars: dict[str, tuple[set[str], int]] = {}

        for child in ast.walk(node):
            if isinstance(child, ast.If):
                referenced = _names(child.test) & params
                if referenced and _has_raise_or_return(child):
                    validated.update(referenced)
            elif isinstance(child, ast.Assert):
                validated.update(_names(child.test) & params)
            elif isinstance(child, ast.Call) and _is_validation_call(child):
                validated.update(_names(child) & params)
            elif isinstance(child, ast.Compare):
                validated.update(_names(child) & params)
            elif isinstance(child, ast.Assign):
                used = _expression_uses_param_in_string(child.value, params)
                if used:
                    for target in child.targets:
                        if isinstance(target, ast.Name):
                            sql_vars[target.id] = (used, child.lineno)
            elif isinstance(child, ast.AnnAssign) and child.value is not None:
                used = _expression_uses_param_in_string(child.value, params)
                if used and isinstance(child.target, ast.Name):
                    sql_vars[child.target.id] = (used, child.lineno)
            elif isinstance(child, ast.Expr) and isinstance(child.value, ast.Call):
                self._inspect_execute_call(child.value, params, validated, sql_vars)
            elif isinstance(child, ast.Call):
                self._inspect_execute_call(child, params, validated, sql_vars)
        self.generic_visit(node)

    def _inspect_execute_call(
        self,
        node: ast.Call,
        params: set[str],
        validated: set[str],
        sql_vars: dict[str, tuple[set[str], int]],
    ) -> None:
        if _call_name(node) != "execute" or not node.args:
            return
        first_arg = node.args[0]
        used: set[str] = set()
        line = getattr(first_arg, "lineno", getattr(node, "lineno", 1))
        if isinstance(first_arg, ast.Name) and first_arg.id in sql_vars:
            used, line = sql_vars[first_arg.id]
        else:
            used = _expression_uses_param_in_string(first_arg, params)
        unvalidated = sorted(used - validated)
        if not unvalidated:
            return
        confidence = Decimal("0.88")
        if confidence < Decimal(str(self.settings.static_review_validation_confidence_threshold)):
            return
        self.findings.append(NormalizedFinding(
            tool="ast-validation",
            rule_id="PY_UNVALIDATED_SQL_PARAMETER",
            file_path=self.file_path,
            start_line=line,
            end_line=line,
            severity=FindingSeverity.MEDIUM,
            category=FindingCategory.VALIDATION,
            title="Parameter reaches SQL execution without clear validation",
            problem="A function parameter appears to influence SQL query construction or execution without an obvious local validation or normalization guard.",
            explanation="This conservative AST rule tracks function parameters within one function and flags clear flows into SQL-sensitive operations. It is not full interprocedural taint analysis.",
            suggestion="Validate or normalize externally supplied parameters before using them in database queries, and pass values through parameterized query arguments.",
            confidence=confidence,
        ))


def analyze(files: list[AnalysisFile], settings: Settings) -> list[NormalizedFinding]:
    findings: list[NormalizedFinding] = []
    for file in files:
        try:
            tree = ast.parse(file.text, filename=file.repository_path)
        except SyntaxError:
            continue
        visitor = ValidationVisitor(file.repository_path, settings)
        visitor.visit(tree)
        findings.extend(visitor.findings)
    return findings
