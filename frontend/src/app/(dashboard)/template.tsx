import { DashboardShell } from "@/components/layout/dashboard-shell";
import { loadDashboard } from "@/lib/api/server";
export default async function Template({
  children,
}: {
  children: React.ReactNode;
}) {
  const result = await loadDashboard();
  return <DashboardShell connected={result.ok}>{children}</DashboardShell>;
}
