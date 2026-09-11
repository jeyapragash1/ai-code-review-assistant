import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired
import tempfile
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.models import (
    FindingCategory,
    FindingSeverity,
    FindingSource,
    PullRequest,
    Repository,
    Review,
    ReviewRisk,
    ReviewStatus,
)
from app.schemas.github import GitHubPullRequestFile
from app.services.static_analysis import ast_validation, bandit, ruff
from app.services.static_analysis.normalize import deduplicate_findings, risk_from_findings
from app.services.static_analysis.review_runner import StaticReviewError, run_static_review
from app.services.static_analysis.review_runner import StaticReviewSummary
from app.services.static_analysis.safety import normalize_repository_path, prepare_analysis_file, should_analyze
from app.services.static_analysis.subprocess import AnalyzerError, AnalyzerTimeoutError, run_analyzer
from app.services.static_analysis.types import AnalysisFile, NormalizedFinding


def settings(**values) -> Settings:
    return Settings(_env_file=None, **values)


def changed_file(**values) -> GitHubPullRequestFile:
    return GitHubPullRequestFile.model_validate({
        "filename": "src/example.py",
        "status": "modified",
        "additions": 1,
        "deletions": 0,
        "changes": 1,
        "patch": "@@",
        **values,
    })


def analysis_file(name: str = "src/example.py", text: str = "print('x')\n") -> AnalysisFile:
    return AnalysisFile(repository_path=name, local_path=str(Path("C:/tmp") / name), content=text.encode(), text=text)


@pytest.mark.parametrize("path", ["/abs.py", "C:/abs.py", "../bad.py", "src/../bad.py", "src\\bad.py", "bad\x00.py"])
def test_rejects_unsafe_repository_paths(path):
    with pytest.raises(ValueError):
        normalize_repository_path(path)


def test_deleted_binary_unsupported_limits_and_renamed_files(tmp_path):
    s = settings(STATIC_REVIEW_MAX_PATCH_BYTES=1024, STATIC_REVIEW_MAX_FILE_BYTES=1024)
    assert should_analyze(changed_file(status="removed"), s) == "deleted_file"
    assert should_analyze(changed_file(filename="README.md"), s) == "unsupported_file_type"
    assert should_analyze(changed_file(patch="x" * 1025), s) == "patch_too_large"
    renamed = changed_file(filename="new/path.py", previous_filename="old/path.py", status="renamed")
    assert should_analyze(renamed, s) is None
    assert prepare_analysis_file(tmp_path, "new/path.py", b"print('x')\n", s).repository_path == "new/path.py"
    with pytest.raises(ValueError, match="file_too_large"):
        prepare_analysis_file(tmp_path, "big.py", b"x" * 1025, s)
    with pytest.raises(ValueError, match="unsupported_encoding"):
        prepare_analysis_file(tmp_path, "bad.py", b"\xff", s)


def test_subprocess_uses_shell_false_and_handles_timeout(monkeypatch, tmp_path):
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return CompletedProcess(args[0], 1, stdout="[]", stderr="")

    monkeypatch.setattr("app.services.static_analysis.subprocess.subprocess.run", fake_run)
    result = asyncio.run(run_analyzer(["python", "-m", "tool"], tmp_path, 1))
    assert result.returncode == 1
    assert calls[0][1]["shell"] is False
    assert calls[0][1]["capture_output"] is True

    def timeout(*args, **kwargs):
        raise TimeoutExpired(args[0], timeout=1)

    monkeypatch.setattr("app.services.static_analysis.subprocess.subprocess.run", timeout)
    with pytest.raises(AnalyzerTimeoutError):
        asyncio.run(run_analyzer(["python", "-m", "tool"], tmp_path, 1))


def test_bandit_sql_injection_normalization(monkeypatch, tmp_path):
    local = tmp_path / "src" / "query.py"
    local.parent.mkdir()
    local.write_text("query = f'SELECT * FROM users WHERE id = {user_id}'\n", encoding="utf-8")
    file = AnalysisFile("src/query.py", str(local), local.read_bytes(), local.read_text())
    output = {
        "results": [{
            "filename": str(local),
            "test_id": "B608",
            "issue_text": "Possible SQL injection vector through string-based query construction.",
            "issue_severity": "MEDIUM",
            "line_number": 1,
        }]
    }
    monkeypatch.setattr("app.services.static_analysis.bandit.run_analyzer", AsyncMock(return_value=Mock(returncode=1, stdout=__import__("json").dumps(output), stderr="")))
    findings = asyncio.run(bandit.analyze([file], tmp_path, settings()))
    assert findings[0].tool == "bandit"
    assert findings[0].severity == FindingSeverity.HIGH
    assert findings[0].category == FindingCategory.SECURITY


def test_bandit_malformed_output_and_crash(monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.static_analysis.bandit.run_analyzer", AsyncMock(return_value=Mock(returncode=1, stdout="not json", stderr="private")))
    with pytest.raises(AnalyzerError):
        asyncio.run(bandit.analyze([analysis_file()], tmp_path, settings()))
    monkeypatch.setattr("app.services.static_analysis.bandit.run_analyzer", AsyncMock(return_value=Mock(returncode=2, stdout="", stderr="private")))
    with pytest.raises(AnalyzerError):
        asyncio.run(bandit.analyze([analysis_file()], tmp_path, settings()))


def test_ruff_broad_exception_normalization(monkeypatch, tmp_path):
    local = tmp_path / "src" / "handler.py"
    local.parent.mkdir()
    local.write_text("try:\n    pass\nexcept Exception:\n    pass\n", encoding="utf-8")
    file = AnalysisFile("src/handler.py", str(local), local.read_bytes(), local.read_text())
    output = [{
        "filename": str(local),
        "code": "BLE001",
        "message": "Do not catch blind exception: `Exception`",
        "location": {"row": 3, "column": 8},
        "end_location": {"row": 3, "column": 17},
    }]
    monkeypatch.setattr("app.services.static_analysis.ruff.run_analyzer", AsyncMock(return_value=Mock(returncode=1, stdout=__import__("json").dumps(output), stderr="")))
    findings = asyncio.run(ruff.analyze([file], tmp_path, settings()))
    assert findings[0].category == FindingCategory.ERROR_HANDLING
    assert findings[0].severity == FindingSeverity.MEDIUM
    assert findings[0].start_line == 3


def test_ruff_malformed_output_and_crash(monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.static_analysis.ruff.run_analyzer", AsyncMock(return_value=Mock(returncode=1, stdout="{}", stderr="private")))
    with pytest.raises(AnalyzerError):
        asyncio.run(ruff.analyze([analysis_file()], tmp_path, settings()))
    monkeypatch.setattr("app.services.static_analysis.ruff.run_analyzer", AsyncMock(return_value=Mock(returncode=2, stdout="", stderr="private")))
    with pytest.raises(AnalyzerError):
        asyncio.run(ruff.analyze([analysis_file()], tmp_path, settings()))


def test_ast_missing_validation_detects_general_unvalidated_sql_flow():
    text = """
def load_account(database, account_identifier):
    sql = f"SELECT id FROM accounts WHERE id = {account_identifier}"
    return database.execute(sql)
"""
    findings = ast_validation.analyze([analysis_file("any/path.py", text)], settings())
    assert len(findings) == 1
    assert findings[0].category == FindingCategory.VALIDATION
    assert findings[0].start_line == 3
    assert "any/path.py" == findings[0].file_path
    assert "fixture" not in findings[0].title.lower()


def test_ast_respects_validation_and_syntax_errors():
    validated = """
def load_account(database, account_identifier):
    if not isinstance(account_identifier, int):
        raise ValueError("bad id")
    sql = f"SELECT id FROM accounts WHERE id = {account_identifier}"
    return database.execute(sql)
"""
    assert ast_validation.analyze([analysis_file("safe.py", validated)], settings()) == []
    assert ast_validation.analyze([analysis_file("broken.py", "def nope(:\n")], settings()) == []


def test_fingerprint_dedup_sorting_and_limit_are_deterministic():
    base = NormalizedFinding(
        tool="bandit",
        rule_id="B608",
        file_path="b.py",
        start_line=2,
        end_line=2,
        severity=FindingSeverity.HIGH,
        category=FindingCategory.SECURITY,
        title="SQL issue",
        problem="x" * 20,
        explanation=None,
        suggestion=None,
        confidence=Decimal("0.8"),
    )
    duplicate_clearer = NormalizedFinding(
        tool="ruff",
        rule_id="B608",
        file_path="b.py",
        start_line=2,
        end_line=2,
        severity=FindingSeverity.HIGH,
        category=FindingCategory.SECURITY,
        title="SQL issue",
        problem="x" * 30,
        explanation=None,
        suggestion=None,
        confidence=Decimal("0.8"),
    )
    other = NormalizedFinding(
        tool="ast-validation",
        rule_id="RULE",
        file_path="a.py",
        start_line=1,
        end_line=1,
        severity=FindingSeverity.MEDIUM,
        category=FindingCategory.VALIDATION,
        title="Validation",
        problem="missing validation",
        explanation=None,
        suggestion=None,
        confidence=Decimal("0.8"),
    )
    result = deduplicate_findings([base, duplicate_clearer, other], settings(STATIC_REVIEW_MAX_FINDINGS=2))
    assert [finding.file_path for finding in result] == ["a.py", "b.py"]
    assert result[1].tool == "ruff"
    assert result[0].fingerprint == deduplicate_findings([other], settings())[0].fingerprint
    assert risk_from_findings(result) == ReviewRisk.HIGH


class FakeTransaction:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        self.session.transactions += 1

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    def __init__(self):
        self.transactions = 0

    def begin(self):
        return FakeTransaction(self)


@dataclass
class FakeReviewState:
    review: Review
    existing: Review | None = None
    findings: list = None


def test_review_state_flow_idempotency_and_force(monkeypatch):
    repo = Repository(id=uuid4(), github_repository_id=1, owner="octocat", name="example", full_name="octocat/example")
    pr = PullRequest(id=uuid4(), repository_id=repo.id, github_pr_number=7, title="PR", author_login="dev",
                     base_branch="main", head_branch="topic", status="open", head_sha="a" * 40)
    state = FakeReviewState(review=Review(id=uuid4(), pull_request_id=pr.id, commit_sha=pr.head_sha, attempt_number=1,
                                          status=ReviewStatus.QUEUED, trigger_type="manual"), findings=[])

    async def fake_pr(*args, **kwargs):
        return pr, repo

    async def fake_existing(self, pull_request_id, commit_sha):
        return state.existing

    async def fake_next(self, pull_request_id, commit_sha):
        return 2 if state.existing else 1

    async def fake_create(self, data):
        state.review.attempt_number = data.attempt_number
        state.review.status = data.status
        return state.review

    async def fake_mark(self, review_id, data):
        state.review.status = data.status
        state.review.overall_risk = data.overall_risk
        return state.review

    async def fake_delete(self, review_id):
        state.findings = []

    async def fake_create_findings(self, findings):
        state.findings = findings
        return len(findings)

    async def fake_summary_counts(self, review_id):
        return 1, {"high": 1}, {"security": 1}

    class FakeClient:
        async def pull_request_files(self, target, number, head_sha):
            return [changed_file(filename="src/app.py")]

        async def file_content(self, target, path, ref, max_bytes):
            return b"def f(x):\n    return x\n"

    monkeypatch.setattr("app.repositories.review.ReviewStore.pull_request_with_repository", fake_pr)
    monkeypatch.setattr("app.repositories.review.ReviewStore.completed_for_commit", fake_existing)
    monkeypatch.setattr("app.repositories.review.ReviewStore.next_attempt_number", fake_next)
    monkeypatch.setattr("app.repositories.review.ReviewStore.create", fake_create)
    monkeypatch.setattr("app.repositories.review.ReviewStore.mark_status", fake_mark)
    monkeypatch.setattr("app.repositories.review.ReviewStore.delete_findings", fake_delete)
    monkeypatch.setattr("app.repositories.review.ReviewStore.finding_summary_counts", fake_summary_counts)
    monkeypatch.setattr("app.repositories.review.ReviewFindingStore.create_idempotent", fake_create_findings)
    monkeypatch.setattr("app.services.static_analysis.review_runner.bandit.analyze", AsyncMock(return_value=[]))
    monkeypatch.setattr("app.services.static_analysis.review_runner.ruff.analyze", AsyncMock(return_value=[]))
    monkeypatch.setattr("app.services.static_analysis.review_runner.ast_validation.analyze", Mock(return_value=[
        NormalizedFinding("ast-validation", "R", "src/app.py", 1, 1, FindingSeverity.LOW, FindingCategory.VALIDATION,
                          "Validation", "Problem", None, None, Decimal("0.8"))
    ]))

    summary = asyncio.run(run_static_review(client=FakeClient(), session=FakeSession(), settings=settings(), repository_full_name="octocat/example", pr_number=7))
    assert summary.final_status == ReviewStatus.COMPLETED
    assert summary.overall_risk == ReviewRisk.LOW
    assert summary.findings_count == 1

    state.existing = Review(id=uuid4(), pull_request_id=pr.id, commit_sha=pr.head_sha, attempt_number=1,
                            status=ReviewStatus.COMPLETED, trigger_type="manual", overall_risk=ReviewRisk.HIGH)
    reused = asyncio.run(run_static_review(client=FakeClient(), session=FakeSession(), settings=settings(), repository_full_name="octocat/example", pr_number=7))
    assert reused.reused is True
    forced = asyncio.run(run_static_review(client=FakeClient(), session=FakeSession(), settings=settings(), repository_full_name="octocat/example", pr_number=7, force=True))
    assert forced.reused is False
    assert state.review.attempt_number == 2


def test_review_failure_marks_failed_and_rolls_back_findings(monkeypatch):
    repo = Repository(id=uuid4(), github_repository_id=1, owner="octocat", name="example", full_name="octocat/example")
    pr = PullRequest(id=uuid4(), repository_id=repo.id, github_pr_number=7, title="PR", author_login="dev",
                     base_branch="main", head_branch="topic", status="open", head_sha="a" * 40)
    review = Review(id=uuid4(), pull_request_id=pr.id, commit_sha=pr.head_sha, attempt_number=1,
                    status=ReviewStatus.QUEUED, trigger_type="manual")
    events = []

    async def fake_pr(*args, **kwargs):
        return pr, repo

    async def fake_existing(self, pull_request_id, commit_sha):
        return None

    async def fake_next(self, pull_request_id, commit_sha):
        return 1

    async def fake_create(self, data):
        return review

    async def fake_mark(self, review_id, data):
        events.append(data.status)
        review.status = data.status
        return review

    async def fake_delete(self, review_id):
        events.append("delete_findings")

    class FakeClient:
        async def pull_request_files(self, target, number, head_sha):
            return [changed_file()]

        async def file_content(self, target, path, ref, max_bytes):
            return b"def f():\n    pass\n"

    monkeypatch.setattr("app.repositories.review.ReviewStore.pull_request_with_repository", fake_pr)
    monkeypatch.setattr("app.repositories.review.ReviewStore.completed_for_commit", fake_existing)
    monkeypatch.setattr("app.repositories.review.ReviewStore.next_attempt_number", fake_next)
    monkeypatch.setattr("app.repositories.review.ReviewStore.create", fake_create)
    monkeypatch.setattr("app.repositories.review.ReviewStore.mark_status", fake_mark)
    monkeypatch.setattr("app.repositories.review.ReviewStore.delete_findings", fake_delete)
    monkeypatch.setattr("app.services.static_analysis.review_runner.bandit.analyze", AsyncMock(side_effect=AnalyzerError("tool failed")))

    with pytest.raises(StaticReviewError) as error:
        asyncio.run(run_static_review(client=FakeClient(), session=FakeSession(), settings=settings(), repository_full_name="octocat/example", pr_number=7))
    assert error.value.code == "static_analyzer_failed"
    assert ReviewStatus.FAILED in events
    assert "delete_findings" in events


def test_review_cli_success_and_failure_exit_codes(monkeypatch, capsys):
    from app.cli import review_pull_request

    class FakeContext:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

    success = StaticReviewSummary(
        review_id=uuid4(),
        pull_request_id=uuid4(),
        repository_full_name="octocat/example",
        pr_number=1,
        commit_sha="a" * 40,
        final_status=ReviewStatus.COMPLETED,
        overall_risk=ReviewRisk.HIGH,
        findings_count=1,
        findings_by_severity={"high": 1},
        findings_by_category={"security": 1},
        skipped_files_by_reason={},
        elapsed_ms=10,
    )

    monkeypatch.setattr("app.clients.github.GitHubClient", lambda settings: FakeContext())
    monkeypatch.setattr("app.db.session.AsyncSessionLocal", lambda: FakeContext())
    monkeypatch.setattr("app.db.session.dispose_db_engine", AsyncMock())
    monkeypatch.setattr("app.services.static_analysis.review_runner.run_static_review", AsyncMock(return_value=success))
    assert asyncio.run(review_pull_request.run("octocat/example", 1, None, False)) == 0
    assert "octocat/example" in capsys.readouterr().out

    monkeypatch.setattr("app.services.static_analysis.review_runner.run_static_review", AsyncMock(side_effect=StaticReviewError("x", "safe failure")))
    assert asyncio.run(review_pull_request.run("octocat/example", 1, None, False)) == 1
    assert "safe failure" in capsys.readouterr().out

    assert asyncio.run(review_pull_request.run(None, None, None, False)) == 1
