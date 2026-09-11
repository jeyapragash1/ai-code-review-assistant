import { get } from "./client.ts";
import { ApiError } from "./errors.ts";
import type { AuthenticatedUser } from "../../types/auth.ts";

function text(value: unknown): string { if (typeof value !== "string") throw new ApiError("unexpected"); return value; }
function nullableText(value: unknown): string | null { return value === null ? null : text(value); }
export function parseAuthenticatedUser(value: unknown): AuthenticatedUser {
  if (!value || typeof value !== "object") throw new ApiError("unexpected");
  const item = value as Record<string, unknown>;
  const id = text(item.id);
  if (!/^[0-9a-f]{8}-/i.test(id) || typeof item.github_user_id !== "number") throw new ApiError("unexpected");
  return { id, github_user_id: item.github_user_id, github_login: text(item.github_login), display_name: nullableText(item.display_name), email: nullableText(item.email), avatar_url: nullableText(item.avatar_url), profile_url: nullableText(item.profile_url), session_expires_at: text(item.session_expires_at) };
}
export const getCurrentUser = (cookie?: string) => get(["auth", "me"], parseAuthenticatedUser, {}, cookie);
export function loginUrl(nextPath = "/dashboard") {
  if (!nextPath.startsWith("/") || nextPath.startsWith("//") || nextPath.includes("\\") || nextPath.includes("%")) throw new ApiError("validation");
  const url = new URL("auth/github/login", process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1/");
  url.searchParams.set("next", nextPath);
  return url.href;
}
