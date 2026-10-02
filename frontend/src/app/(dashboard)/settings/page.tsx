import { loadDashboard } from "@/lib/api/server";
import { apiOrigin } from "@/lib/config";
import { SettingsView } from "@/components/settings/settings-view";
import { getCurrentUser } from "@/lib/api/auth";
import { backendCookie } from "@/lib/api/server";
import { GitHubSettings } from "@/components/settings/github-settings";
export default async function Page() {
  const result = await loadDashboard();
  const user = await getCurrentUser(await backendCookie());
  return (
    <div className="page-stack"><SettingsView
      connected={result.ok}
      repositoryCount={
        result.ok ? result.data.connected_repository_count : null
      }
      apiOrigin={apiOrigin()}
      user={user}
    /><GitHubSettings /></div>
  );
}
