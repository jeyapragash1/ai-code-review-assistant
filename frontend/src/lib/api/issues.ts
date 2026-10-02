import type { PaginationQuery } from "../../types/api.ts";
import { get } from "./client.ts";
import { isUuid, parseIssue, parsePage } from "./parsers.ts";
import { ApiError } from "./errors.ts";

export interface IssueQuery extends PaginationQuery {
  repository_id?: string;
  state?: "open" | "closed";
  search?: string;
  author?: string;
  assignee?: string;
  label?: string;
}
export const getIssues = (query: IssueQuery = {}) => get(["issues"], (value) => parsePage(value, parseIssue), { ...query });
export function getIssue(id: string) {
  if (!isUuid(id)) throw new ApiError("not_found");
  return get(["issues", id], parseIssue);
}
