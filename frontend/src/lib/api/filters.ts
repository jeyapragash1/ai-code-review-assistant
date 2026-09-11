import type { SearchParams } from "../../types/api.ts";
import type { Query } from "./client.ts";
import { ApiError } from "./errors.ts";
import { isUuid } from "./parsers.ts";
import type { PullRequestStatus } from "../../types/pull-request.ts";
import type {
  FindingCategory,
  FindingSeverity,
  FindingSource,
  FindingStatus,
  ReviewRisk,
  ReviewStatus,
} from "../../types/review.ts";
export function one(params: SearchParams, key: string): string | undefined {
  const value = params[key];
  if (Array.isArray(value)) throw new ApiError("validation");
  return value || undefined;
}
export function paginationQuery(params: SearchParams) {
  const page = Number(one(params, "page") ?? 1),
    page_size = Number(one(params, "page_size") ?? 20);
  if (
    !Number.isInteger(page) ||
    page < 1 ||
    page > 1_000_000 ||
    !Number.isInteger(page_size) ||
    page_size < 1 ||
    page_size > 100
  )
    throw new ApiError("validation");
  return { page, page_size };
}
export function searchQuery(params: SearchParams): string | undefined {
  const search = one(params, "search");
  if (search && search.length > 200) throw new ApiError("validation");
  return search;
}
export function statusQuery(
  params: SearchParams,
): PullRequestStatus | undefined {
  const status = one(params, "status");
  if (
    status === undefined ||
    status === "open" ||
    status === "closed" ||
    status === "merged"
  )
    return status;
  throw new ApiError("validation");
}
export function activeQuery(params: SearchParams): boolean | undefined {
  const value = one(params, "is_active");
  if (value === undefined) return undefined;
  if (value !== "true" && value !== "false") throw new ApiError("validation");
  return value === "true";
}
export function repositoryQuery(params: SearchParams): string | undefined {
  const id = one(params, "repository_id");
  if (id && !isUuid(id)) throw new ApiError("validation");
  return id;
}
export function pullRequestQuery(params: SearchParams): string | undefined {
  const id = one(params, "pull_request_id");
  if (id && !isUuid(id)) throw new ApiError("validation");
  return id;
}
export function reviewStatusQuery(
  params: SearchParams,
): ReviewStatus | undefined {
  const status = one(params, "status");
  if (
    status === undefined ||
    status === "queued" ||
    status === "fetching" ||
    status === "static_analysis" ||
    status === "ai_analysis" ||
    status === "validating" ||
    status === "publishing" ||
    status === "completed" ||
    status === "failed"
  )
    return status;
  throw new ApiError("validation");
}
export function reviewRiskQuery(params: SearchParams): ReviewRisk | undefined {
  const risk = one(params, "overall_risk");
  if (
    risk === undefined ||
    risk === "none" ||
    risk === "low" ||
    risk === "medium" ||
    risk === "high"
  )
    return risk;
  throw new ApiError("validation");
}
export function commitShaQuery(params: SearchParams): string | undefined {
  const sha = one(params, "commit_sha");
  if (sha && !/^[0-9a-f]{7,40}$/i.test(sha)) throw new ApiError("validation");
  return sha;
}
export function findingSeverityQuery(
  params: SearchParams,
): FindingSeverity | undefined {
  const severity = one(params, "severity");
  if (
    severity === undefined ||
    severity === "high" ||
    severity === "medium" ||
    severity === "low"
  )
    return severity;
  throw new ApiError("validation");
}
export function findingCategoryQuery(
  params: SearchParams,
): FindingCategory | undefined {
  const category = one(params, "category");
  if (
    category === undefined ||
    category === "security" ||
    category === "bug" ||
    category === "validation" ||
    category === "error_handling" ||
    category === "performance" ||
    category === "database" ||
    category === "maintainability" ||
    category === "code_quality" ||
    category === "best_practice"
  )
    return category;
  throw new ApiError("validation");
}
export function findingStatusQuery(
  params: SearchParams,
): FindingStatus | undefined {
  const status = one(params, "status");
  if (
    status === undefined ||
    status === "open" ||
    status === "dismissed" ||
    status === "resolved"
  )
    return status;
  throw new ApiError("validation");
}
export function findingSourceQuery(
  params: SearchParams,
): FindingSource | undefined {
  const source = one(params, "source");
  if (
    source === undefined ||
    source === "static" ||
    source === "ai" ||
    source === "hybrid"
  )
    return source;
  throw new ApiError("validation");
}
export function filePathQuery(params: SearchParams): string | undefined {
  const filePath = one(params, "file_path");
  if (filePath && filePath.length > 1024) throw new ApiError("validation");
  return filePath;
}
export function pageHref(path: string, query: Query, page: number): string {
  const url = new URL(path, "http://local.invalid");
  const values: Query = { ...query, page };
  for (const [key, value] of Object.entries(values))
    if (value !== undefined && value !== "")
      url.searchParams.set(key, String(value));
  return url.pathname + url.search;
}
