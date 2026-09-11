import { apiBase } from "../config.ts";
import { ApiError, statusError } from "./errors.ts";

export type Query = Record<string, string | number | boolean | undefined>;
export function apiUrl(
  segments: readonly string[],
  query: Query = {},
  base: URL = apiBase(),
): URL {
  if (segments.some((s) => !s || s === "." || s === ".."))
    throw new ApiError("validation");
  const url = new URL(segments.map(encodeURIComponent).join("/"), base);
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined) url.searchParams.set(key, String(value));
  }
  return url;
}
export async function get<T>(
  segments: readonly string[],
  parse: (value: unknown) => T,
  query: Query = {},
  cookie?: string,
): Promise<T> {
  if (!cookie) {
    try {
      const nextHeaders = await import("next/headers");
      cookie = (await nextHeaders.cookies()).toString();
    } catch {
      // Non-Next runtimes, including transport tests, have no request cookie.
    }
  }
  const url = apiUrl(segments, query);
  let response: Response;
  try {
    response = await fetch(url, {
      method: "GET",
      headers: { Accept: "application/json", ...(cookie ? { Cookie: cookie } : {}) },
      credentials: "omit",
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
  } catch {
    throw new ApiError("unavailable");
  }
  if (!response.ok) {
    // Consume JSON defensively, but never surface backend detail or raw response text.
    try {
      await response.json();
    } catch {
      /* Non-JSON errors have the same safe status mapping. */
    }
    throw statusError(response.status);
  }
  try {
    const data: unknown = await response.json();
    return parse(data);
  } catch {
    throw new ApiError("unexpected");
  }
}
