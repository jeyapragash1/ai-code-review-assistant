import { proxyPost } from "@/lib/api/mutations";
import { isUuid } from "@/lib/api/parsers";
export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!isUuid(id)) return Response.json({ status: "failed" }, { status: 400 });
  return proxyPost(request, ["pull-requests", id, "review-jobs"]);
}
