import { cache } from "react";
import { connection } from "next/server";
import { cookies } from "next/headers";
import { getDashboard } from "./dashboard";
import { errorKind, type ApiErrorKind } from "./errors";
export type Result<T> =
  { ok: true; data: T } | { ok: false; error: ApiErrorKind };
export async function load<T>(request: () => Promise<T>): Promise<Result<T>> {
  await connection();
  try {
    return { ok: true, data: await request() };
  } catch (error) {
    return { ok: false, error: errorKind(error) };
  }
}
// Request-scoped memoization shares the connectivity read with dashboard/settings pages.
export const loadDashboard = cache(() => load(getDashboard));
export async function backendCookie(): Promise<string> {
  const cookie = (await cookies()).get("codereview_session");
  return cookie ? `${cookie.name}=${cookie.value}` : "";
}
