export interface Issue {
  id: string;
  repository_id: string;
  repository_full_name: string;
  github_issue_id: number;
  github_issue_number: number;
  title: string;
  body: string | null;
  state: "open" | "closed";
  state_reason: string | null;
  author_login: string | null;
  author_github_id: number | null;
  assignees: unknown[];
  labels: unknown[];
  is_locked: boolean;
  comment_count: number;
  html_url: string;
  github_created_at: string;
  github_updated_at: string;
  github_closed_at: string | null;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
}
