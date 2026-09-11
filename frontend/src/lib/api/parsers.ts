import type { Page } from "../../types/api.ts";
import type { Repository, RepositorySummary } from "../../types/repository.ts";
import type {
  PullRequest,
  PullRequestDetail,
  PullRequestStatus,
} from "../../types/pull-request.ts";
import type { DashboardStatistics } from "../../types/dashboard.ts";
import { ApiError } from "./errors.ts";

function fail(): never {
  throw new ApiError("unexpected");
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
export function parsePullRequestDetail(v: unknown): PullRequestDetail {
  const o = record(v);
  return { ...parsePullRequest(o), repository: summary(o.repository) };
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
    reviews_count: num(o.reviews_count),
    findings_count: num(o.findings_count),
    high_severity_findings_count: num(o.high_severity_findings_count),
    recently_updated_pull_requests: array(
      o.recently_updated_pull_requests,
      parsePullRequest,
    ),
  };
}
