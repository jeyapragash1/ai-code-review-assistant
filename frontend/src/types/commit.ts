export interface Commit {
  id: string;
  repository_id: string;
  repository_full_name: string;
  sha: string;
  title: string;
  message: string | null;
  author_name: string | null;
  author_login: string | null;
  committer_name: string | null;
  committer_login: string | null;
  authored_at: string | null;
  committed_at: string | null;
  html_url: string | null;
  parent_count: number;
  reference: string | null;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
}