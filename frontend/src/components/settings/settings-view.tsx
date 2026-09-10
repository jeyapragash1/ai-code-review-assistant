"use client";
import { useSyncExternalStore } from "react";
import { useTheme } from "next-themes";
import { Badge, PageHeading, Select } from "@/components/ui";
import { RefreshButton } from "@/components/ui/refresh-button";
const subscribe = () => () => {};
export function SettingsView({
  connected,
  repositoryCount,
  apiOrigin,
}: {
  connected: boolean;
  repositoryCount: number | null;
  apiOrigin: string;
}) {
  const { theme, setTheme } = useTheme();
  const mounted = useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
  return (
    <div className="page-stack max-w-4xl">
      <PageHeading
        title="Settings"
        description="Local appearance and backend connection information."
        action={<RefreshButton />}
      />
      <section className="border-b border-[var(--border)] pb-6">
        <h2 className="section-title mb-4">Appearance</h2>
        <div className="max-w-sm">
          <Select
            label="Theme preference"
            value={mounted ? theme : "dark"}
            onChange={(e) => setTheme(e.target.value)}
          >
            <option value="dark">Dark</option>
            <option value="light">Light</option>
            <option value="system">System</option>
          </Select>
        </div>
        <p className="muted mt-3 text-xs">Saved in this browser only.</p>
      </section>
      <section className="border-b border-[var(--border)] pb-6">
        <h2 className="section-title mb-4">Backend connection</h2>
        <dl className="space-y-4">
          <div>
            <dt className="muted text-xs">API origin</dt>
            <dd className="break-safe mt-1 font-mono text-sm">{apiOrigin}</dd>
          </div>
          <div>
            <dt className="muted mb-1 text-xs">Connection status</dt>
            <dd>
              <Badge tone={connected ? "active" : "pending"}>
                {connected ? "Live API" : "API unavailable"}
              </Badge>
            </dd>
          </div>
          <div>
            <dt className="muted text-xs">Connected repositories</dt>
            <dd className="mt-1">{repositoryCount ?? "Not available"}</dd>
          </div>
        </dl>
      </section>
      {[
        "GitHub App installation",
        "AI review configuration",
        "Notification preferences",
      ].map((name) => (
        <section
          key={name}
          className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] pb-6"
        >
          <h2 className="section-title">{name}</h2>
          <Badge>Not configured</Badge>
        </section>
      ))}
      <section>
        <h2 className="section-title">Data and privacy</h2>
        <p className="muted mt-3 text-sm leading-7">
          This workspace reads synchronized backend data. GitHub synchronization
          is an administrative CLI operation. Review processing and
          notifications are available in a later phase. Credentials are never
          displayed here.
        </p>
      </section>
    </div>
  );
}
