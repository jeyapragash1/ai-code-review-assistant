import type { PaginationQuery } from "../../types/api.ts";
import type { PullRequestStatus } from "../../types/pull-request.ts";
import { get } from "./client.ts";
import { ApiError } from "./errors.ts";
import {
  isUuid,
  parsePage,
  parsePullRequest,
  parsePullRequestDetail,
} from "./parsers.ts";
export interface PullRequestQuery extends PaginationQuery {
  search?: string;
  repository_id?: string;
  status?: PullRequestStatus;
}
export const getPullRequests = (query: PullRequestQuery = {}) =>
  get(["pull-requests"], (v) => parsePage(v, parsePullRequest), { ...query });
export function getPullRequest(id: string) {
  if (!isUuid(id)) throw new ApiError("not_found");
  return get(["pull-requests", id], parsePullRequestDetail);
}
