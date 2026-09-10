import type { RepositorySummary } from "./repository.ts";
export type PullRequestStatus = "open" | "closed" | "merged";
export interface PullRequest {
  id: string;
  repository_id: string;
  repository_full_name: string;
  github_pr_number: number;
  title: string;
  author_login: string;
  base_branch: string;
  head_branch: string;
  status: PullRequestStatus;
  is_draft: boolean | null;
  head_sha: string;
  html_url: string | null;
  additions: number | null;
  deletions: number | null;
  changed_files: number | null;
  github_created_at: string | null;
  github_updated_at: string | null;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
}
export interface PullRequestDetail extends PullRequest {
  repository: RepositorySummary;
}
