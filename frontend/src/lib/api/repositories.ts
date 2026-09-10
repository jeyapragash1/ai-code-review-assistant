import type { PaginationQuery } from "../../types/api.ts";
import type { PullRequestStatus } from "../../types/pull-request.ts";
import { get } from "./client.ts";
import { ApiError } from "./errors.ts";
import {
  isUuid,
  parsePage,
  parsePullRequest,
  parseRepository,
} from "./parsers.ts";
export interface RepositoryQuery extends PaginationQuery {
  search?: string;
  is_active?: boolean;
}
export const getRepositories = (query: RepositoryQuery = {}) =>
  get(["repositories"], (v) => parsePage(v, parseRepository), { ...query });
export function getRepository(id: string) {
  if (!isUuid(id)) throw new ApiError("not_found");
  return get(["repositories", id], parseRepository);
}
export function getRepositoryPullRequests(
  id: string,
  query: PaginationQuery & { status?: PullRequestStatus } = {},
) {
  if (!isUuid(id)) throw new ApiError("not_found");
  return get(
    ["repositories", id, "pull-requests"],
    (v) => parsePage(v, parsePullRequest),
    { ...query },
  );
}
