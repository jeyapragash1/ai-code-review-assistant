import { apiUrl } from "./client";
import { backendCookie } from "./server";

export async function proxyPost(request: Request, segments: string[]) {
  const origin = request.headers.get("origin");
  let source: URL;
  try { source = new URL(origin ?? ""); } catch { return Response.json({ status: "failed" }, { status: 403 }); }
  // Next may reconstruct request.url with its internal hostname. Browser Host
  // identifies the actual target; the backend additionally checks exact Origin.
  if (!origin || source.origin !== origin || !["http:", "https:"].includes(source.protocol) || source.host !== request.headers.get("host")) return Response.json({ status: "failed" }, { status: 403 });
  try {
    const response = await fetch(apiUrl(segments), { method: "POST", headers: { Cookie: await backendCookie(), Origin: origin, Accept: "application/json" }, cache: "no-store", signal: AbortSignal.timeout(120000) });
    // Never forward backend error detail, credentials, cookies or raw payloads.
    return Response.json({ status: response.ok ? "accepted" : "failed" }, { status: response.status, headers: { "Cache-Control": "no-store" } });
  } catch { return Response.json({ status: "failed" }, { status: 503 }); }
}
