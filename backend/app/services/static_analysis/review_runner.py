from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
import tempfile
import time
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.errors import GitHubError
from app.clients.github import GitHubClient
from app.core.config import Settings
from app.models import PullRequest, Repository, ReviewRisk, ReviewStatus, ReviewTriggerType
from app.repositories.review import ReviewFindingStore, ReviewStore
from app.schemas.github import RepositoryTarget
from app.schemas.review import ReviewCreate, ReviewFindingCreate, ReviewStatusUpdate
from app.services.static_analysis import ast_validation, bandit, ruff
from app.services.static_analysis.normalize import deduplicate_findings, risk_from_findings
from app.services.static_analysis.safety import prepare_analysis_file, should_analyze, skipped
from app.services.static_analysis.subprocess import AnalyzerError
from app.services.static_analysis.types import AnalysisFile, NormalizedFinding, SkippedFile


class StaticReviewError(Exception):
    def __init__(self, code: str, message: str, review_id: UUID | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.review_id = review_id


class StaticReviewSummary(BaseModel):
    review_id: UUID
    pull_request_id: UUID
    repository_full_name: str
    pr_number: int
    commit_sha: str
    reused: bool = False
    forced: bool = False
    final_status: ReviewStatus
    overall_risk: ReviewRisk | None
    findings_count: int
    findings_by_severity: dict[str, int] = Field(default_factory=dict)
    findings_by_category: dict[str, int] = Field(default_factory=dict)
    skipped_files_by_reason: dict[str, int] = Field(default_factory=dict)
    elapsed_ms: int

    @property
    def short_commit_sha(self) -> str:
        return self.commit_sha[:12]


def _finding_create(review_id: UUID, finding: NormalizedFinding) -> ReviewFindingCreate:
    return ReviewFindingCreate(
        review_id=review_id,
        file_path=finding.file_path,
        start_line=finding.start_line,
        end_line=finding.end_line,
        diff_side=finding.diff_side,
        severity=finding.severity,
        category=finding.category,
        title=finding.title,
        problem=finding.problem,
        explanation=finding.explanation,
        suggestion=finding.suggestion,
        confidence=finding.confidence.quantize(Decimal("0.0001")),
        source=finding.source,
        fingerprint=finding.fingerprint,
        code_snippet=None,
    )


def _counts(findings: list[NormalizedFinding]) -> tuple[dict[str, int], dict[str, int]]:
    severity = Counter(finding.severity.value for finding in findings)
    category = Counter(finding.category.value for finding in findings)
    return dict(sorted(severity.items())), dict(sorted(category.items()))


def _skip_counts(skipped_files: list[SkippedFile]) -> dict[str, int]:
    return dict(sorted(Counter(item.reason for item in skipped_files).items()))


def _summary(
    review_id: UUID,
    pull_request: PullRequest,
    repository: Repository,
    *,
    reused: bool,
    forced: bool,
    status: ReviewStatus,
    risk: ReviewRisk | None,
    findings: list[NormalizedFinding],
    skipped_files: list[SkippedFile],
    started: float,
) -> StaticReviewSummary:
    severity, category = _counts(findings)
    return StaticReviewSummary(
        review_id=review_id,
        pull_request_id=pull_request.id,
        repository_full_name=repository.full_name,
        pr_number=pull_request.github_pr_number,
        commit_sha=pull_request.head_sha,
        reused=reused,
        forced=forced,
        final_status=status,
        overall_risk=risk,
        findings_count=len(findings),
        findings_by_severity=severity,
        findings_by_category=category,
        skipped_files_by_reason=_skip_counts(skipped_files),
        elapsed_ms=max(0, int((time.perf_counter() - started) * 1000)),
    )


async def _mark(session: AsyncSession, review_id: UUID, update: ReviewStatusUpdate) -> None:
    async with session.begin():
        await ReviewStore(session).mark_status(review_id, update)


async def _prepare_files(
    client: GitHubClient,
    target: RepositoryTarget,
    pull_request: PullRequest,
    root: Path,
    settings: Settings,
) -> tuple[list[AnalysisFile], list[SkippedFile]]:
    metadata = await client.pull_request_files(target, pull_request.github_pr_number, pull_request.head_sha)
    analysis_files: list[AnalysisFile] = []
    skipped_files: list[SkippedFile] = []
    total_bytes = 0

    for index, item in enumerate(metadata):
        if index >= settings.static_review_max_changed_files:
            skipped_files.append(skipped(item.filename, "too_many_changed_files"))
            continue
        reason = should_analyze(item, settings)
        if reason is not None:
            skipped_files.append(skipped(item.filename, reason))
            continue
        path = item.filename
        try:
            content = await client.file_content(target, path, pull_request.head_sha, settings.static_review_max_file_bytes)
        except GitHubError:
            skipped_files.append(skipped(path, "content_unavailable"))
            continue
        if b"\x00" in content:
            skipped_files.append(skipped(path, "binary_file"))
            continue
        if total_bytes + len(content) > settings.static_review_max_total_bytes:
            skipped_files.append(skipped(path, "total_bytes_limit"))
            continue
        try:
            file = prepare_analysis_file(root, path, content, settings)
        except ValueError as exc:
            skipped_files.append(skipped(path, str(exc) or "unsafe_file"))
            continue
        analysis_files.append(file)
        total_bytes += len(content)
    return analysis_files, skipped_files


async def run_static_review(
    *,
    client: GitHubClient,
    session: AsyncSession,
    settings: Settings,
    pull_request_id: UUID | None = None,
    repository_full_name: str | None = None,
    pr_number: int | None = None,
    force: bool = False,
) -> StaticReviewSummary:
    started = time.perf_counter()
    review_id: UUID | None = None
    pull_request: PullRequest | None = None
    repository: Repository | None = None
    findings: list[NormalizedFinding] = []
    skipped_files: list[SkippedFile] = []

    try:
        async with session.begin():
            store = ReviewStore(session)
            row = await store.pull_request_with_repository(
                pull_request_id=pull_request_id,
                repository_full_name=repository_full_name,
                pr_number=pr_number,
                lock=True,
            )
            if row is None:
                raise StaticReviewError("pull_request_not_found", "Pull Request was not found in PostgreSQL.")
            pull_request, repository = row
            existing = await store.completed_for_commit(pull_request.id, pull_request.head_sha)
            if existing is not None and not force:
                total, severity, category = await store.finding_summary_counts(existing.id)
                return StaticReviewSummary(
                    review_id=existing.id,
                    pull_request_id=pull_request.id,
                    repository_full_name=repository.full_name,
                    pr_number=pull_request.github_pr_number,
                    commit_sha=pull_request.head_sha,
                    reused=True,
                    forced=force,
                    final_status=existing.status,
                    overall_risk=existing.overall_risk,
                    findings_count=total,
                    findings_by_severity=severity,
                    findings_by_category=category,
                    skipped_files_by_reason={},
                    elapsed_ms=max(0, int((time.perf_counter() - started) * 1000)),
                )
            attempt = await store.next_attempt_number(pull_request.id, pull_request.head_sha)
            review = await store.create(ReviewCreate(
                pull_request_id=pull_request.id,
                commit_sha=pull_request.head_sha,
                attempt_number=attempt,
                status=ReviewStatus.QUEUED,
                trigger_type=ReviewTriggerType.MANUAL,
                started_at=datetime.now(UTC),
            ))
            review_id = review.id

        target = RepositoryTarget(owner=repository.owner, repo=repository.name)
        await _mark(session, review_id, ReviewStatusUpdate(status=ReviewStatus.FETCHING))

        with tempfile.TemporaryDirectory(prefix="ai-code-review-static-") as temporary:
            root = Path(temporary)
            analysis_files, skipped_files = await _prepare_files(client, target, pull_request, root, settings)
            await _mark(session, review_id, ReviewStatusUpdate(status=ReviewStatus.STATIC_ANALYSIS))
            static_started = time.perf_counter()
            analyzer_findings = []
            analyzer_findings.extend(await bandit.analyze(analysis_files, root, settings))
            analyzer_findings.extend(await ruff.analyze(analysis_files, root, settings))
            analyzer_findings.extend(ast_validation.analyze(analysis_files, settings))
            static_duration_ms = max(0, int((time.perf_counter() - static_started) * 1000))
            await _mark(session, review_id, ReviewStatusUpdate(status=ReviewStatus.VALIDATING))
            findings = deduplicate_findings(analyzer_findings, settings)

        risk = risk_from_findings(findings)
        elapsed_ms = max(0, int((time.perf_counter() - started) * 1000))
        async with session.begin():
            review_store = ReviewStore(session)
            finding_store = ReviewFindingStore(session)
            await review_store.delete_findings(review_id)
            await finding_store.create_idempotent([_finding_create(review_id, finding) for finding in findings])
            await review_store.mark_status(
                review_id,
                ReviewStatusUpdate(
                    status=ReviewStatus.COMPLETED,
                    overall_risk=risk,
                    duration_ms=elapsed_ms,
                    static_analysis_duration_ms=static_duration_ms,
                    ai_analysis_duration_ms=0,
                    completed_at=datetime.now(UTC),
                ),
            )
        return _summary(
            review_id,
            pull_request,
            repository,
            reused=False,
            forced=force,
            status=ReviewStatus.COMPLETED,
            risk=risk,
            findings=findings,
            skipped_files=skipped_files,
            started=started,
        )
    except IntegrityError as exc:
        raise StaticReviewError("duplicate_review_attempt", "A review attempt already exists for this Pull Request commit.", review_id) from exc
    except (GitHubError, AnalyzerError, SQLAlchemyError, StaticReviewError) as exc:
        if isinstance(exc, StaticReviewError):
            code, message = exc.code, exc.message
        elif isinstance(exc, GitHubError):
            code, message = "github_unavailable", str(exc)
        elif isinstance(exc, AnalyzerError):
            code, message = "static_analyzer_failed", str(exc)
        else:
            code, message = "database_error", "Review persistence failed."
        if review_id is not None:
            try:
                async with session.begin():
                    store = ReviewStore(session)
                    await store.delete_findings(review_id)
                    await store.mark_status(
                        review_id,
                        ReviewStatusUpdate(
                            status=ReviewStatus.FAILED,
                            error_code=code,
                            error_message=message,
                            duration_ms=max(0, int((time.perf_counter() - started) * 1000)),
                            completed_at=datetime.now(UTC),
                        ),
                    )
            except SQLAlchemyError:
                pass
        raise StaticReviewError(code, message, review_id) from None
