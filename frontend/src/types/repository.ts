export interface RepositorySummary {
  id: string;
  full_name: string;
  html_url: string | null;
}
export interface Repository extends RepositorySummary {
  github_repository_id: number;
  owner: string;
  name: string;
  description: string | null;
  default_branch: string;
  primary_language: string | null;
  is_private: boolean | null;
  is_active: boolean;
  pull_request_count: number;
  open_pull_request_count: number;
  github_updated_at: string | null;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
}
