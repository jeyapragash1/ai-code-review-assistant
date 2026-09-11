from __future__ import annotations

from dataclasses import replace

from app.core.config import Settings
from app.models.enums import FindingCategory, FindingSeverity, ReviewRisk
from app.services.static_analysis.types import NormalizedFinding


def clean_text(value: str | None, limit: int) -> str | None:
    if value is None:
        return None
    text = " ".join(value.replace("\x00", "").split())
    return text[:limit] if text else None


def sanitize_finding(finding: NormalizedFinding, settings: Settings) -> NormalizedFinding:
    return replace(
        finding,
        title=clean_text(finding.title, settings.static_review_max_title_length) or "Static analysis finding",
        problem=clean_text(finding.problem, settings.static_review_max_problem_length) or "A static analyzer reported this issue.",
        explanation=clean_text(finding.explanation, settings.static_review_max_explanation_length),
        suggestion=clean_text(finding.suggestion, settings.static_review_max_suggestion_length),
        confidence=max(0, min(finding.confidence, 1)),
    ).with_fingerprint()


def deduplicate_findings(findings: list[NormalizedFinding], settings: Settings) -> list[NormalizedFinding]:
    by_key: dict[tuple[str, int | None, FindingCategory], NormalizedFinding] = {}
    severity_rank = {FindingSeverity.HIGH: 3, FindingSeverity.MEDIUM: 2, FindingSeverity.LOW: 1}
    for finding in findings:
        sanitized = sanitize_finding(finding, settings)
        key = (sanitized.file_path, sanitized.start_line, sanitized.category)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = sanitized
            continue
        existing_score = severity_rank[existing.severity], len(existing.problem), existing.tool != "ruff"
        incoming_score = severity_rank[sanitized.severity], len(sanitized.problem), sanitized.tool != "ruff"
        if incoming_score > existing_score:
            by_key[key] = sanitized
    return sorted(
        by_key.values(),
        key=lambda item: (item.file_path, item.start_line or 0, item.category.value, item.severity.value, item.title),
    )[: settings.static_review_max_findings]


def risk_from_findings(findings: list[NormalizedFinding]) -> ReviewRisk:
    severities = {finding.severity for finding in findings}
    if FindingSeverity.HIGH in severities:
        return ReviewRisk.HIGH
    if FindingSeverity.MEDIUM in severities:
        return ReviewRisk.MEDIUM
    if FindingSeverity.LOW in severities:
        return ReviewRisk.LOW
    return ReviewRisk.NONE
