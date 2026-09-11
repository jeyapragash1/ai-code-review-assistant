import type { PullRequestDetail, PullRequestStatus } from "./pull-request.ts";

export const REVIEW_STATUSES = [
  "queued",
  "fetching",
  "static_analysis",
  "ai_analysis",
  "validating",
  "publishing",
  "completed",
  "failed",
] as const;
export type ReviewStatus = (typeof REVIEW_STATUSES)[number];

export const REVIEW_RISKS = ["none", "low", "medium", "high"] as const;
export type ReviewRisk = (typeof REVIEW_RISKS)[number];

export const REVIEW_TRIGGER_TYPES = [
  "manual",
  "webhook",
  "synchronization",
] as const;
export type ReviewTriggerType = (typeof REVIEW_TRIGGER_TYPES)[number];

export const FINDING_SEVERITIES = ["high", "medium", "low"] as const;
export type FindingSeverity = (typeof FINDING_SEVERITIES)[number];

export const FINDING_CATEGORIES = [
  "security",
  "bug",
  "validation",
  "error_handling",
  "performance",
  "database",
  "maintainability",
  "code_quality",
  "best_practice",
] as const;
export type FindingCategory = (typeof FINDING_CATEGORIES)[number];

export const FINDING_SOURCES = ["static", "ai", "hybrid"] as const;
export type FindingSource = (typeof FINDING_SOURCES)[number];

export const FINDING_STATUSES = ["open", "dismissed", "resolved"] as const;
export type FindingStatus = (typeof FINDING_STATUSES)[number];

export type FindingDiffSide = "left" | "right";

export interface Review {
  id: string;
  pull_request_id: string;
  repository_id: string | null;
  repository_full_name: string | null;
  pull_request_number: number | null;
  pull_request_title: string | null;
  pull_request_status: PullRequestStatus | null;
  commit_sha: string;
  attempt_number: number;
  status: ReviewStatus;
  overall_risk: ReviewRisk | null;
  trigger_type: ReviewTriggerType;
  model_name: string | null;
  model_version: string | null;
  prompt_version: string | null;
  duration_ms: number | null;
  static_analysis_duration_ms: number | null;
  ai_analysis_duration_ms: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  total_tokens: number | null;
  estimated_cost_usd: string | null;
  error_code: string | null;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
  findings_count: number;
  high_severity_findings_count: number;
  created_at: string;
  updated_at: string;
}

export interface ReviewDetail extends Review {
  pull_request: PullRequestDetail;
}

export interface ReviewFinding {
  id: string;
  review_id: string;
  file_path: string;
  start_line: number | null;
  end_line: number | null;
  diff_side: FindingDiffSide | null;
  severity: FindingSeverity;
  category: FindingCategory;
  title: string;
  problem: string;
  explanation: string | null;
  suggestion: string | null;
  confidence: string;
  source: FindingSource;
  fingerprint: string;
  code_snippet: string | null;
  status: FindingStatus;
  github_comment_id: number | null;
  published_to_github: boolean;
  created_at: string;
  updated_at: string;
}
