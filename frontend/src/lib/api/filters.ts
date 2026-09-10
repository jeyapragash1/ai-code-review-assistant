import type { SearchParams } from "../../types/api.ts";
import type { Query } from "./client.ts";
import { ApiError } from "./errors.ts";
import { isUuid } from "./parsers.ts";
import type { PullRequestStatus } from "../../types/pull-request.ts";
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
export function pageHref(path: string, query: Query, page: number): string {
  const url = new URL(path, "http://local.invalid");
  const values: Query = { ...query, page };
  for (const [key, value] of Object.entries(values))
    if (value !== undefined && value !== "")
      url.searchParams.set(key, String(value));
  return url.pathname + url.search;
}
