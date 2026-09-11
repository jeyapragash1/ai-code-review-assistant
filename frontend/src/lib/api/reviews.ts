import type { PaginationQuery } from "../../types/api.ts";
import type {
  FindingCategory,
  FindingSeverity,
  FindingSource,
  FindingStatus,
  ReviewRisk,
  ReviewStatus,
} from "../../types/review.ts";
import { get } from "./client.ts";
import { ApiError } from "./errors.ts";
import {
  isUuid,
  parsePage,
  parseReview,
  parseReviewDetail,
  parseReviewFinding,
} from "./parsers.ts";

export interface ReviewQuery extends PaginationQuery {
  pull_request_id?: string;
  repository_id?: string;
  status?: ReviewStatus;
  overall_risk?: ReviewRisk;
  commit_sha?: string;
}

export interface FindingQuery extends PaginationQuery {
  severity?: FindingSeverity;
  category?: FindingCategory;
  status?: FindingStatus;
  source?: FindingSource;
  file_path?: string;
}

export const getReviews = (query: ReviewQuery = {}) =>
  get(["reviews"], (v) => parsePage(v, parseReview), { ...query });

export function getReview(id: string) {
  if (!isUuid(id)) throw new ApiError("not_found");
  return get(["reviews", id], parseReviewDetail);
}

export function getReviewFindings(id: string, query: FindingQuery = {}) {
  if (!isUuid(id)) throw new ApiError("not_found");
  return get(["reviews", id, "findings"], (v) => parsePage(v, parseReviewFinding), {
    ...query,
  });
}

export function getReviewFinding(id: string) {
  if (!isUuid(id)) throw new ApiError("not_found");
  return get(["review-findings", id], parseReviewFinding);
}
