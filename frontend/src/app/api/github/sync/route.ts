import { proxyPost } from "@/lib/api/mutations";
export async function POST(request: Request) { return proxyPost(request, ["github", "sync"]); }
