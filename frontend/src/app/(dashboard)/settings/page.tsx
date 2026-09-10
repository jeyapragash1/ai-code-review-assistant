import { loadDashboard } from "@/lib/api/server";
import { apiOrigin } from "@/lib/config";
import { SettingsView } from "@/components/settings/settings-view";
export default async function Page() {
  const result = await loadDashboard();
  return (
    <SettingsView
      connected={result.ok}
      repositoryCount={
        result.ok ? result.data.connected_repository_count : null
      }
      apiOrigin={apiOrigin()}
    />
  );
}
