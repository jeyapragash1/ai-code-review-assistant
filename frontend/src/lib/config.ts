import { ApiError } from "./api/errors.ts";

export function normalizeApiBase(value: string): URL {
  try {
    const url = new URL(value.trim());
    if (
      !["http:", "https:"].includes(url.protocol) ||
      url.username ||
      url.password ||
      url.search ||
      url.hash
    )
      throw new Error();
    url.pathname = url.pathname.replace(/\/+$/, "") + "/";
    return url;
  } catch {
    throw new ApiError("unexpected");
  }
}
export function apiBase(): URL {
  return normalizeApiBase(
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1",
  );
}
export function apiOrigin(): string {
  try {
    return apiBase().origin;
  } catch {
    return "Not configured";
  }
}
