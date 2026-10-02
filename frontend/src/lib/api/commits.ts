import type { PaginationQuery } from "../../types/api.ts";
import { get } from "./client.ts";
import { parseCommit, parsePage } from "./parsers.ts";
export const getCommits = (query: PaginationQuery & { repository_id?: string } = {}) => get(["commits"], (value) => parsePage(value, parseCommit), { ...query });
