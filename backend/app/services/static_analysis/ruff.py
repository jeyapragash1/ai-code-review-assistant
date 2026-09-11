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

RUFF_RULES = ["BLE001"]


def _line(location: Any) -> int | None:
    if isinstance(location, dict):
        row = location.get("row")
        if isinstance(row, int) and row > 0:
            return row
    return None


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
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--isolated",
            "--select",
            ",".join(RUFF_RULES),
            "--output-format",
            "json",
            str(root),
        ],
        root,
        settings.static_review_analyzer_timeout_seconds,
    )
    if result.returncode not in {0, 1}:
        raise AnalyzerError("Ruff failed during static analysis.")
    if not result.stdout.strip():
        return []
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise AnalyzerError("Ruff returned malformed output.") from None
    if not isinstance(payload, list):
        raise AnalyzerError("Ruff returned malformed output.")

    findings: list[NormalizedFinding] = []
    for diagnostic in payload:
        if not isinstance(diagnostic, dict):
            continue
        file_path = _relative(str(diagnostic.get("filename", "")), files)
        if file_path is None:
            continue
        code = diagnostic.get("code") if isinstance(diagnostic.get("code"), str) else None
        message = diagnostic.get("message") if isinstance(diagnostic.get("message"), str) else "Ruff reported a static analysis issue."
        line = _line(diagnostic.get("location"))
        category = FindingCategory.ERROR_HANDLING if code == "BLE001" else FindingCategory.CODE_QUALITY
        findings.append(NormalizedFinding(
            tool="ruff",
            rule_id=code,
            file_path=file_path,
            start_line=line,
            end_line=_line(diagnostic.get("end_location")) or line,
            severity=FindingSeverity.MEDIUM if code == "BLE001" else FindingSeverity.LOW,
            category=category,
            title=f"Ruff {code}: {message}" if code else message,
            problem=message,
            explanation="Ruff reported this diagnostic using application-selected rules with repository configuration disabled.",
            suggestion="Narrow the exception handling or address the reported diagnostic in a way that preserves useful failures.",
            confidence=Decimal("0.9"),
        ))
    return findings
