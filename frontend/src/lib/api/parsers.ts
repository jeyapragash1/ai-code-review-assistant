import type { Page } from "../../types/api.ts";
import type { Repository, RepositorySummary } from "../../types/repository.ts";
import type { Issue } from "../../types/issue.ts";
import type { Commit } from "../../types/commit.ts";
import type {
  PullRequest,
  PullRequestDetail,
  PullRequestStatus,
} from "../../types/pull-request.ts";
import type { DashboardStatistics } from "../../types/dashboard.ts";
import type {
  FindingCategory,
  FindingDiffSide,
  FindingSeverity,
  FindingSource,
  FindingStatus,
  Review,
  ReviewDetail,
  ReviewFinding,
  ReviewRisk,
  ReviewStatus,
  ReviewTriggerType,
} from "../../types/review.ts";
import { ApiError } from "./errors.ts";

function fail(): never {
  throw new ApiError("unexpected");
}
export function parseActivity(v: unknown) {
  const o = record(v);
  return { id: uuid(o.id), repository_id: nullable(o.repository_id, uuid), installation_id: nullable(o.installation_id, uuid),
    actor_login: nullable(o.actor_login, str), event_type: str(o.event_type), event_action: nullable(o.event_action, str),
    event_at: date(o.event_at), received_at: date(o.received_at), processing_status: str(o.processing_status),
    retry_count: num(o.retry_count), error_message: nullable(o.error_message, str) };
}
export function parseSyncStatus(v: unknown) {
  const o = record(v);
  return { app_configured: bool(o.app_configured), private_key_configured: bool(o.private_key_configured),
    webhook_configured: bool(o.webhook_configured), installation_count: num(o.installation_count),
    accessible_repository_count: num(o.accessible_repository_count), last_synchronized_at: nullable(o.last_synchronized_at, date),
    last_result: nullable(o.last_result, str), safe_error: nullable(o.safe_error, str) };
}
export function parseInstallations(v: unknown) {
  return array(v, value => { const o = record(value); return { id: num(o.id), account_login: str(o.account_login),
    is_active: bool(o.is_active), repository_count: num(o.repository_count), last_synced_at: nullable(o.last_synced_at, date) }; });
}
export function parseReviewJob(v: unknown) {
  if (v === null) return null;
  const o = record(v), status = str(o.status);
  if (!["queued", "processing", "completed", "failed", "retryable"].includes(status)) fail();
  return { id: uuid(o.id), head_sha: str(o.head_sha), status, retry_count: num(o.retry_count),
    review_id: nullable(o.review_id, uuid), error_message: nullable(o.error_message, str) };
}
export function parseAccountStatistics(v: unknown) {
  const o = record(v);
  function counts(value: unknown) { const r = record(value); return Object.fromEntries(Object.entries(r).map(([key, value]) => [key, num(value)])); }
  const c = counts(o.counts);
  for (const key of ["repositories_total", "repositories_public", "repositories_private", "repositories_fork", "repositories_archived", "repositories_inactive", "pull_requests_total", "pull_requests_open", "pull_requests_closed", "pull_requests_merged", "pull_requests_draft", "issues_total", "issues_open", "issues_closed", "recent_commits", "captured_push_events", "recent_activity", "review_jobs_queued", "review_jobs_processing", "review_jobs_completed", "review_jobs_failed", "review_jobs_retryable", "reviews_completed", "findings_total", "findings_high"]) num(c[key]);
  function repo(value: unknown) { const r = record(value); return { id: uuid(r.id), full_name: str(r.full_name) }; }
  return { counts: c, since: date(o.since), until: date(o.until), activity_metric: str(o.activity_metric),
    findings_by_severity: counts(o.findings_by_severity), findings_by_category: counts(o.findings_by_category), findings_by_repository: counts(o.findings_by_repository),
    recently_updated_repositories: array(o.recently_updated_repositories, value => { const r = record(value); return { ...repo(r), github_updated_at: nullable(r.github_updated_at, date), github_pushed_at: nullable(r.github_pushed_at, date), last_synced_at: nullable(r.last_synced_at, date) }; }),
    most_active_repositories: array(o.most_active_repositories, value => { const r = record(value); return { ...repo(r), activity_count: num(r.activity_count) }; }),
    recent_commits: array(o.recent_commits, value => { const r = record(value); return { id: uuid(r.id), repository_id: uuid(r.repository_id), sha: str(r.sha), title: str(r.title), committed_at: nullable(r.committed_at, date) }; }),
    recent_activity: array(o.recent_activity, value => { const r = record(value); return { id: uuid(r.id), repository_id: nullable(r.repository_id, uuid), event_type: str(r.event_type), actor_login: nullable(r.actor_login, str), event_at: date(r.event_at) }; }),
  };
}
function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}
function record(v: unknown): Record<string, unknown> {
  return isRecord(v) ? v : fail();
}
function str(v: unknown): string {
  return typeof v === "string" ? v : fail();
}
function num(v: unknown): number {
  return typeof v === "number" && Number.isSafeInteger(v) && v >= 0
    ? v
    : fail();
}
function bool(v: unknown): boolean {
  return typeof v === "boolean" ? v : fail();
}
function decimalString(v: unknown): string {
  if (typeof v === "string" && /^(?:0|[1-9]\d*)(?:\.\d+)?$/.test(v))
    return v;
  if (typeof v === "number" && Number.isFinite(v) && v >= 0)
    return String(v);
  return fail();
}
function nullable<T>(v: unknown, parse: (v: unknown) => T): T | null {
  return v === null ? null : parse(v);
}
function date(v: unknown): string {
  const s = str(v);
  return /(?:Z|[+-]\d\d:\d\d)$/.test(s) && Number.isFinite(Date.parse(s))
    ? s
    : fail();
}
export function isUuid(v: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
    v,
  );
}
function uuid(v: unknown): string {
  const s = str(v);
  return isUuid(s) ? s : fail();
}
function array<T>(v: unknown, parse: (v: unknown) => T): T[] {
  return Array.isArray(v) ? v.map(parse) : fail();
}
export function parseStatus(v: unknown): PullRequestStatus {
  return v === "open" || v === "closed" || v === "merged" ? v : fail();
}
export function parseReviewStatus(v: unknown): ReviewStatus {
  return v === "queued" ||
    v === "fetching" ||
    v === "static_analysis" ||
    v === "ai_analysis" ||
    v === "validating" ||
    v === "publishing" ||
    v === "completed" ||
    v === "failed"
    ? v
    : fail();
}
export function parseReviewRisk(v: unknown): ReviewRisk {
  return v === "none" || v === "low" || v === "medium" || v === "high"
    ? v
    : fail();
}
export function parseReviewTrigger(v: unknown): ReviewTriggerType {
  return v === "manual" || v === "webhook" || v === "synchronization"
    ? v
    : fail();
}
export function parseFindingSeverity(v: unknown): FindingSeverity {
  return v === "high" || v === "medium" || v === "low" ? v : fail();
}
export function parseFindingCategory(v: unknown): FindingCategory {
  return v === "security" ||
    v === "bug" ||
    v === "validation" ||
    v === "error_handling" ||
    v === "performance" ||
    v === "database" ||
    v === "maintainability" ||
    v === "code_quality" ||
    v === "best_practice"
    ? v
    : fail();
}
export function parseFindingSource(v: unknown): FindingSource {
  return v === "static" || v === "ai" || v === "hybrid" ? v : fail();
}
export function parseFindingStatus(v: unknown): FindingStatus {
  return v === "open" || v === "dismissed" || v === "resolved"
    ? v
    : fail();
}
function parseDiffSide(v: unknown): FindingDiffSide {
  return v === "left" || v === "right" ? v : fail();
}
function summary(v: unknown): RepositorySummary {
  const o = record(v);
  return {
    id: uuid(o.id),
    full_name: str(o.full_name),
    html_url: nullable(o.html_url, str),
  };
}
export function parseRepository(v: unknown): Repository {
  const o = record(v);
  return {
    ...summary(o),
    github_repository_id: num(o.github_repository_id),
    owner: str(o.owner),
    name: str(o.name),
    description: nullable(o.description, str),
    default_branch: str(o.default_branch),
    primary_language: nullable(o.primary_language, str),
    is_private: nullable(o.is_private, bool),
    is_active: bool(o.is_active),
    pull_request_count: num(o.pull_request_count),
    open_pull_request_count: num(o.open_pull_request_count),
    github_updated_at: nullable(o.github_updated_at, date),
    last_synced_at: nullable(o.last_synced_at, date),
    created_at: date(o.created_at),
    updated_at: date(o.updated_at),
  };
}
export function parsePullRequest(v: unknown): PullRequest {
  const o = record(v);
  return {
    id: uuid(o.id),
    repository_id: uuid(o.repository_id),
    repository_full_name: str(o.repository_full_name),
    github_pr_number: num(o.github_pr_number),
    title: str(o.title),
    author_login: str(o.author_login),
    base_branch: str(o.base_branch),
    head_branch: str(o.head_branch),
    status: parseStatus(o.status),
    is_draft: nullable(o.is_draft, bool),
    head_sha: str(o.head_sha),
    html_url: nullable(o.html_url, str),
    additions: nullable(o.additions, num),
    deletions: nullable(o.deletions, num),
    changed_files: nullable(o.changed_files, num),
    github_created_at: nullable(o.github_created_at, date),
    github_updated_at: nullable(o.github_updated_at, date),
    last_synced_at: nullable(o.last_synced_at, date),
    created_at: date(o.created_at),
    updated_at: date(o.updated_at),
  };
}
export function parseIssue(v: unknown): Issue {
  const o = record(v);
  const state = o.state === "open" || o.state === "closed" ? o.state : fail();
  return {
    id: uuid(o.id), repository_id: uuid(o.repository_id), repository_full_name: str(o.repository_full_name),
    github_issue_id: num(o.github_issue_id), github_issue_number: num(o.github_issue_number), title: str(o.title),
    body: nullable(o.body, str), state, state_reason: nullable(o.state_reason, str), author_login: nullable(o.author_login, str),
    author_github_id: nullable(o.author_github_id, num), assignees: Array.isArray(o.assignees) ? o.assignees : fail(),
    labels: Array.isArray(o.labels) ? o.labels : fail(), is_locked: bool(o.is_locked), comment_count: num(o.comment_count),
    html_url: str(o.html_url), github_created_at: date(o.github_created_at), github_updated_at: date(o.github_updated_at),
    github_closed_at: nullable(o.github_closed_at, date), last_synced_at: nullable(o.last_synced_at, date),
    created_at: date(o.created_at), updated_at: date(o.updated_at),
  };
}
export function parseCommit(v: unknown): Commit {
  const o = record(v);
  if (!/^[0-9a-f]{40}$/i.test(str(o.sha))) fail();
  return { id: uuid(o.id), repository_id: uuid(o.repository_id), repository_full_name: str(o.repository_full_name), sha: str(o.sha), title: str(o.title), message: nullable(o.message, str), author_name: nullable(o.author_name, str), author_login: nullable(o.author_login, str), committer_name: nullable(o.committer_name, str), committer_login: nullable(o.committer_login, str), authored_at: nullable(o.authored_at, date), committed_at: nullable(o.committed_at, date), html_url: nullable(o.html_url, str), parent_count: num(o.parent_count), reference: nullable(o.reference, str), last_synced_at: nullable(o.last_synced_at, date), created_at: date(o.created_at), updated_at: date(o.updated_at) };
}
export function parsePullRequestDetail(v: unknown): PullRequestDetail {
  const o = record(v);
  return { ...parsePullRequest(o), repository: summary(o.repository) };
}
export function parseReview(v: unknown): Review {
  const o = record(v);
  return {
    id: uuid(o.id),
    pull_request_id: uuid(o.pull_request_id),
    repository_id: nullable(o.repository_id, uuid),
    repository_full_name: nullable(o.repository_full_name, str),
    pull_request_number: nullable(o.pull_request_number, num),
    pull_request_title: nullable(o.pull_request_title, str),
    pull_request_status: nullable(o.pull_request_status, parseStatus),
    commit_sha: str(o.commit_sha),
    attempt_number: num(o.attempt_number),
    status: parseReviewStatus(o.status),
    overall_risk: nullable(o.overall_risk, parseReviewRisk),
    trigger_type: parseReviewTrigger(o.trigger_type),
    model_name: nullable(o.model_name, str),
    model_version: nullable(o.model_version, str),
    prompt_version: nullable(o.prompt_version, str),
    duration_ms: nullable(o.duration_ms, num),
    static_analysis_duration_ms: nullable(o.static_analysis_duration_ms, num),
    ai_analysis_duration_ms: nullable(o.ai_analysis_duration_ms, num),
    input_tokens: nullable(o.input_tokens, num),
    output_tokens: nullable(o.output_tokens, num),
    total_tokens: nullable(o.total_tokens, num),
    estimated_cost_usd: nullable(o.estimated_cost_usd, decimalString),
    error_code: nullable(o.error_code, str),
    error_message: nullable(o.error_message, str),
    started_at: date(o.started_at),
    completed_at: nullable(o.completed_at, date),
    findings_count: num(o.findings_count),
    high_severity_findings_count: num(o.high_severity_findings_count),
    created_at: date(o.created_at),
    updated_at: date(o.updated_at),
  };
}
export function parseReviewDetail(v: unknown): ReviewDetail {
  const o = record(v);
  return { ...parseReview(o), pull_request: parsePullRequestDetail(o.pull_request) };
}
export function parseReviewFinding(v: unknown): ReviewFinding {
  const o = record(v);
  const confidence = decimalString(o.confidence);
  const value = Number(confidence);
  if (!Number.isFinite(value) || value < 0 || value > 1) fail();
  return {
    id: uuid(o.id),
    review_id: uuid(o.review_id),
    file_path: str(o.file_path),
    start_line: nullable(o.start_line, num),
    end_line: nullable(o.end_line, num),
    diff_side: nullable(o.diff_side, parseDiffSide),
    severity: parseFindingSeverity(o.severity),
    category: parseFindingCategory(o.category),
    title: str(o.title),
    problem: str(o.problem),
    explanation: nullable(o.explanation, str),
    suggestion: nullable(o.suggestion, str),
    confidence,
    source: parseFindingSource(o.source),
    fingerprint: str(o.fingerprint),
    code_snippet: nullable(o.code_snippet, str),
    status: parseFindingStatus(o.status),
    github_comment_id: nullable(o.github_comment_id, num),
    published_to_github: bool(o.published_to_github),
    created_at: date(o.created_at),
    updated_at: date(o.updated_at),
  };
}
export function parsePage<T>(v: unknown, parse: (v: unknown) => T): Page<T> {
  const o = record(v);
  const result = {
    items: array(o.items, parse),
    total: num(o.total),
    page: num(o.page),
    page_size: num(o.page_size),
    total_pages: num(o.total_pages),
  };
  if (
    result.page < 1 ||
    result.page_size < 1 ||
    result.page_size > 100 ||
    result.total_pages !== Math.ceil(result.total / result.page_size) ||
    result.items.length > result.page_size
  )
    fail();
  return result;
}
export function parseDashboard(v: unknown): DashboardStatistics {
  const o = record(v);
  return {
    connected_repository_count: num(o.connected_repository_count),
    total_pull_request_count: num(o.total_pull_request_count),
    open_pr_count: num(o.open_pr_count),
    closed_pr_count: num(o.closed_pr_count),
    merged_pr_count: num(o.merged_pr_count),
    total_reviews: num(o.total_reviews),
    completed_reviews: num(o.completed_reviews),
    failed_reviews: num(o.failed_reviews),
    in_progress_reviews: num(o.in_progress_reviews),
    total_findings: num(o.total_findings),
    high_severity_findings: num(o.high_severity_findings),
    reviews_count: num(o.reviews_count),
    findings_count: num(o.findings_count),
    high_severity_findings_count: num(o.high_severity_findings_count),
    recently_updated_pull_requests: array(
      o.recently_updated_pull_requests,
      parsePullRequest,
    ),
  };
}
