import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/api/auth";
import { backendCookie, load } from "@/lib/api/server";
export default async function Layout({ children }: { children: React.ReactNode }) {
  const result = await load(async () => getCurrentUser(await backendCookie()));
  if (!result.ok && result.error === "unauthenticated") redirect("/login?next=/dashboard");
  if (!result.ok && result.error === "unavailable") return <div className="p-8">Authentication service unavailable. Start FastAPI and refresh.</div>;
  return children;
}
