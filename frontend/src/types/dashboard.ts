import type { PullRequest } from "./pull-request.ts";
export interface DashboardStatistics {
  connected_repository_count: number;
  total_pull_request_count: number;
  open_pr_count: number;
  closed_pr_count: number;
  merged_pr_count: number;
  reviews_count: number;
  findings_count: number;
  high_severity_findings_count: number;
  recently_updated_pull_requests: PullRequest[];
}
