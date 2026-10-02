import Link from "next/link";
import { get } from "@/lib/api/client";
import { parseAccountStatistics } from "@/lib/api/parsers";
import { load } from "@/lib/api/server";
import { ApiState } from "@/components/ui/api-state";
import { one } from "@/lib/api/filters";
import type { SearchParams } from "@/types/api";

export async function AccountDashboard({ filters = {}, repositoryId }: { filters?: SearchParams; repositoryId?: string }) {
  const result = await load(async () => {
    const query = { repository_id: repositoryId ?? one(filters, "repository_id"), since: one(filters, "since"), until: one(filters, "until") };
    return { query, stats: await get(["dashboard", "account-statistics"], parseAccountStatistics, query) };
  });
  if (!result.ok) return <ApiState kind={result.error} />;
  const d = result.data.stats, query = result.data.query;
  const linkQuery = repositoryId ? `?repository_id=${encodeURIComponent(repositoryId)}` : "";
  return <section className="page-stack" aria-label="Account-wide GitHub statistics">
    {repositoryId && <p className="text-sm">Access state: {d.counts.repositories_inactive > 0 ? "Inactive or revoked" : d.counts.repositories_total > 0 ? "Authorized local data" : "Unavailable"}</p>}
    {!repositoryId && <form className="flex flex-wrap gap-3" action="/dashboard">{(["repository_id", "since", "until"] as const).map(key => <label key={key} className="text-sm">{key.replaceAll("_", " ")}<input name={key} defaultValue={query[key] ?? ""} className="block rounded border border-[var(--border)] bg-[var(--surface)] p-2" placeholder={key === "repository_id" ? "Repository UUID" : "ISO date with timezone"} /></label>)}<button className="button" type="submit">Apply filters</button></form>}
    <p className="muted text-sm">Recent commits and activity: {d.since} to {d.until}. Default period: 30 days. Other totals cover all synchronized records.</p>
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{[
      { title: "Repositories", href: "/repositories", keys: ["repositories_total", "repositories_public", "repositories_private", "repositories_fork", "repositories_archived", "repositories_inactive"] },
      { title: "Pull Requests", href: "/pull-requests", keys: ["pull_requests_total", "pull_requests_open", "pull_requests_draft", "pull_requests_closed", "pull_requests_merged"] },
      { title: "Issues", href: "/issues", keys: ["issues_total", "issues_open", "issues_closed"] },
      { title: "Commits and activity", href: "/activity", keys: ["recent_commits", "captured_push_events", "recent_activity"] },
      { title: "Review queue", href: "/reviews", keys: ["review_jobs_queued", "review_jobs_processing", "review_jobs_completed", "review_jobs_failed", "review_jobs_retryable", "reviews_completed"] },
      { title: "Findings", href: "/reviews", keys: ["findings_total", "findings_high"] },
    ].map(section => <section className="panel p-5" key={section.title}><h2 className="section-title"><Link href={section.href + linkQuery}>{section.title}</Link></h2><dl className="mt-3 space-y-2">{section.keys.map(key => <div key={key} className="flex justify-between gap-3"><dt className="muted text-sm">{key.replaceAll("_", " ")}</dt><dd className="font-semibold tabular-nums">{d.counts[key]}</dd></div>)}</dl></section>)}</div>
    <div className="grid gap-4 lg:grid-cols-2"><section className="panel p-5"><h2 className="section-title">Recent commits</h2>{d.recent_commits.length === 0 ? <p className="muted mt-3">No synchronized commits in this period.</p> : <ul className="mt-3 space-y-2">{d.recent_commits.map(c => <li key={c.id}><Link href={`/commits?repository_id=${c.repository_id}`}>{c.title}</Link><p className="muted text-xs">{c.sha.slice(0, 12)} · {c.committed_at}</p></li>)}</ul>}</section>
    <section className="panel p-5"><h2 className="section-title">Recent webhook activity</h2>{d.recent_activity.length === 0 ? <p className="muted mt-3">Permanent activity begins when webhook delivery is enabled and processed.</p> : <ul className="mt-3 space-y-2">{d.recent_activity.map(e => <li key={e.id}><Link href={`/activity${e.repository_id ? `?repository_id=${e.repository_id}` : ""}`}>{e.event_type} · {e.actor_login ?? "Unknown actor"}</Link><p className="muted text-xs">{e.event_at}</p></li>)}</ul>}</section></div>
    <div className="grid gap-4 lg:grid-cols-2"><section className="panel p-5"><h2 className="section-title">Recently updated repositories</h2>{d.recently_updated_repositories.length === 0 ? <p className="muted mt-3">No authorized repositories synchronized.</p> : <ul className="mt-3 space-y-2">{d.recently_updated_repositories.map(r => <li key={r.id}><Link href={`/repositories/${r.id}`}>{r.full_name}</Link><p className="muted text-xs">Updated: {r.github_updated_at ?? "Unknown"} · Pushed: {r.github_pushed_at ?? "Unknown"} · Sync: {r.last_synced_at ?? "Never"}</p></li>)}</ul>}</section>
    <section className="panel p-5"><h2 className="section-title">Most active repositories</h2><p className="muted my-3 text-xs">{d.activity_metric}</p>{d.most_active_repositories.length === 0 ? <p className="muted">No activity in this period.</p> : <ul className="space-y-2">{d.most_active_repositories.map(r => <li key={r.id}><Link href={`/repositories/${r.id}`}>{r.full_name}</Link> · {r.activity_count}</li>)}</ul>}</section></div>
    <section className="panel p-5"><h2 className="section-title">Findings breakdown</h2><div className="mt-3 grid gap-4 sm:grid-cols-3">{[["Severity", d.findings_by_severity], ["Category", d.findings_by_category], ["Repository", d.findings_by_repository]].map(([label, values]) => <div key={String(label)}><h3>{String(label)}</h3>{Object.entries(values).length === 0 ? <p className="muted">No findings</p> : <ul>{Object.entries(values).map(([key, value]) => <li className="break-safe text-sm" key={key}>{key}: {value}</li>)}</ul>}</div>)}</div></section>
  </section>;
}
