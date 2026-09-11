import { DashboardShell } from "@/components/layout/dashboard-shell";
import { loadDashboard } from "@/lib/api/server";
import { getCurrentUser } from "@/lib/api/auth";
import { backendCookie, load } from "@/lib/api/server";
export default async function Template({
  children,
}: {
  children: React.ReactNode;
}) {
  const [result, user] = await Promise.all([loadDashboard(), load(async () => getCurrentUser(await backendCookie()))]);
  if (!user.ok) return children;
  return <DashboardShell connected={result.ok} user={user.data}>{children}</DashboardShell>;
}
