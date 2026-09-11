from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.models.enums import FindingCategory, FindingSeverity
from app.services.static_analysis.subprocess import AnalyzerError, run_analyzer
from app.services.static_analysis.types import AnalysisFile, NormalizedFinding


def _severity(value: str, test_id: str | None) -> FindingSeverity:
    if test_id == "B608":
        return FindingSeverity.HIGH
    normalized = value.lower()
    if normalized == "high":
        return FindingSeverity.HIGH
    if normalized == "medium":
        return FindingSeverity.MEDIUM
    return FindingSeverity.LOW


def _category(test_id: str | None, text: str) -> FindingCategory:
    lowered = text.lower()
    if test_id in {"B608", "B102", "B307", "B602", "B603", "B604", "B605", "B606", "B607"}:
        return FindingCategory.SECURITY
    if "exception" in lowered or test_id in {"B110", "B112"}:
        return FindingCategory.ERROR_HANDLING
    if "assert" in lowered:
        return FindingCategory.BUG
    return FindingCategory.CODE_QUALITY


def _line(value: Any) -> int | None:
    return value if isinstance(value, int) and value > 0 else None


def _relative(filename: str, files: list[AnalysisFile]) -> str | None:
    candidate = Path(filename)
    if not candidate.is_absolute():
        relative = candidate.as_posix()
        for item in files:
            if item.repository_path == relative:
                return item.repository_path
    normalized = str(candidate.resolve())
    for item in files:
        if str(Path(item.local_path).resolve()) == normalized:
            return item.repository_path
    return None


async def analyze(files: list[AnalysisFile], root: Path, settings: Settings) -> list[NormalizedFinding]:
    if not files:
        return []
    result = await run_analyzer(
        [sys.executable, "-m", "bandit", "-r", str(root), "-f", "json", "-q"],
        root,
        settings.static_review_analyzer_timeout_seconds,
    )
    if result.returncode not in {0, 1}:
        raise AnalyzerError("Bandit failed during static analysis.")
    if not result.stdout.strip():
        return []
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise AnalyzerError("Bandit returned malformed output.") from None
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        raise AnalyzerError("Bandit returned malformed output.")

    findings: list[NormalizedFinding] = []
    for issue in results:
        if not isinstance(issue, dict):
            continue
        file_path = _relative(str(issue.get("filename", "")), files)
        if file_path is None:
            continue
        test_id = issue.get("test_id") if isinstance(issue.get("test_id"), str) else None
        issue_text = issue.get("issue_text") if isinstance(issue.get("issue_text"), str) else "Bandit reported a security issue."
        line = _line(issue.get("line_number"))
        findings.append(NormalizedFinding(
            tool="bandit",
            rule_id=test_id,
            file_path=file_path,
            start_line=line,
            end_line=line,
            severity=_severity(str(issue.get("issue_severity", "")), test_id),
            category=_category(test_id, issue_text),
            title=f"Bandit {test_id}: {issue_text}" if test_id else issue_text,
            problem=issue_text,
            explanation="Bandit reported this issue from static inspection of the Pull Request head revision.",
            suggestion="Review the affected code and use a safer implementation appropriate for the reported Bandit rule.",
            confidence=Decimal("0.85"),
        ))
    return findings
