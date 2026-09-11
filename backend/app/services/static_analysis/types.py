from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
import hashlib
import json

from app.models.enums import FindingCategory, FindingDiffSide, FindingSeverity, FindingSource


@dataclass(frozen=True)
class AnalysisFile:
    repository_path: str
    local_path: str
    content: bytes
    text: str


@dataclass(frozen=True)
class SkippedFile:
    path: str
    reason: str


@dataclass(frozen=True)
class NormalizedFinding:
    tool: str
    rule_id: str | None
    file_path: str
    start_line: int | None
    end_line: int | None
    severity: FindingSeverity
    category: FindingCategory
    title: str
    problem: str
    explanation: str | None
    suggestion: str | None
    confidence: Decimal
    source: FindingSource = FindingSource.STATIC
    diff_side: FindingDiffSide | None = FindingDiffSide.RIGHT
    fingerprint: str = ""

    def with_fingerprint(self) -> "NormalizedFinding":
        material = {
            "category": self.category.value,
            "file_path": self.file_path,
            "rule_id": self.rule_id or "",
            "severity": self.severity.value,
            "source": self.source.value,
            "start_line": self.start_line or 0,
            "title": self.title.strip().lower(),
            "tool": self.tool.strip().lower(),
        }
        fingerprint = hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        return replace(self, fingerprint=fingerprint)


@dataclass(frozen=True)
class StaticAnalysisResult:
    findings: list[NormalizedFinding]
    skipped_files: list[SkippedFile]
