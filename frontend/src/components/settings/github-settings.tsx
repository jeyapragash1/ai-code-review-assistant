import { get } from "@/lib/api/client";
import { parseSyncStatus, parseInstallations } from "@/lib/api/parsers";
import { load } from "@/lib/api/server";
import { ApiState } from "@/components/ui/api-state";
import { JobButton } from "@/components/ui/job-button";

export async function GitHubSettings() {
  const result = await load(async () => ({ status: await get(["github", "sync", "status"], parseSyncStatus), installations: await get(["github", "installations"], parseInstallations) }));
  if (!result.ok) return <ApiState kind={result.error} />;
  const { status: s, installations } = result.data;
  return <section className="panel p-5"><h2 className="section-title">GitHub synchronization</h2><dl className="my-4 grid gap-4 sm:grid-cols-2">{[
    ["App configuration", s.app_configured ? "Ready" : "Unavailable"], ["Webhook configuration", s.webhook_configured ? "Ready" : "Unavailable"],
    ["Accessible repositories", s.accessible_repository_count], ["Last synchronization", s.last_synchronized_at ?? "Never"],
    ["Last result", s.last_result ?? "No synchronization recorded"], ["Synchronization error", s.safe_error ?? "None"],
  ].map(([name, value]) => <div key={name}><dt className="muted text-xs">{name}</dt><dd>{value}</dd></div>)}</dl>
    {installations.length === 0 ? <p className="muted">No installation for this account has been synchronized.</p> : <ul className="my-4 space-y-2">{installations.map(i => <li key={i.id}>{i.account_login} · {i.is_active ? "Active" : "Suspended or removed"} · {i.repository_count} repositories · {i.last_synced_at ?? "Never synchronized"}</li>)}</ul>}
    <JobButton endpoint="/api/github/sync" label="Sync GitHub" disabled={!s.app_configured} />
  </section>;
}
