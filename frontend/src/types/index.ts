export type Severity = "high" | "medium" | "low";
export type FindingCategory =
  "Security" | "Validation" | "Reliability" | "Maintainability";
export type ReviewStatus = "completed" | "processing" | "failed";
export type PullRequestStatus = "open" | "closed" | "merged";
export interface Repository {
  id: string;
  owner: string;
  name: string;
  description: string;
  language: string;
  defaultBranch: string;
  isActive: boolean;
}
export interface PullRequest {
  id: string;
  repositoryId: string;
  number: number;
  title: string;
  author: string;
  baseBranch: string;
  headBranch: string;
  status: PullRequestStatus;
  headSha: string;
  filesChanged: number;
  additions: number;
  deletions: number;
}
export interface Review {
  id: string;
  pullRequestId: string;
  status: ReviewStatus;
  summary: string;
  createdAt: string;
  commitSha: string;
  staticSeconds: number;
  aiSeconds: number;
}
export interface ReviewFinding {
  id: string;
  reviewId: string;
  severity: Severity;
  category: FindingCategory;
  source: "Static Analysis" | "AI" | "Hybrid";
  file: string;
  startLine: number;
  endLine: number;
  title: string;
  problem: string;
  impact: string;
  suggestion: string;
  confidence: number;
  snippet: string;
}
export interface DashboardStatistics {
  repositories: number;
  reviewedPullRequests: number;
  findings: number;
  highSeverityFindings: number;
}
export interface ReviewActivityPoint {
  date: string;
  reviews: number;
  findings: number;
}
