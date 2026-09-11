export interface AuthenticatedUser {
  id: string;
  github_user_id: number;
  github_login: string;
  display_name: string | null;
  email: string | null;
  avatar_url: string | null;
  profile_url: string | null;
  session_expires_at: string;
}
