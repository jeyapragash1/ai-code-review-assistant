import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const api = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
  try {
    const response = await fetch(new URL("auth/logout", api.endsWith("/") ? api : `${api}/`), { method: "POST", headers: { Cookie: request.headers.get("cookie") ?? "", Origin: new URL(request.url).origin }, cache: "no-store" });
    const result = NextResponse.redirect(new URL("/login", request.url), 303);
    const cookie = response.headers.get("set-cookie");
    if (cookie) result.headers.set("set-cookie", cookie);
    return result;
  } catch { return NextResponse.redirect(new URL("/login?error=logout_failed", request.url), 303); }
}
