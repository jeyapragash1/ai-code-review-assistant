import Link from "next/link";
import type { SearchParams } from "@/types/api";
import { load } from "@/lib/api/server";
import { getActivity } from "@/lib/api/activity";
import { paginationQuery, one } from "@/lib/api/filters";
import { ApiState } from "@/components/ui/api-state";
import { EmptyState, PageHeading } from "@/components/ui";
import { Pagination } from "@/components/ui/pagination";
import { RefreshButton } from "@/components/ui/refresh-button";

export default async function Page({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const params = await searchParams;
  const result = await load(async () => {
    const query = { ...paginationQuery(params), repository_id: one(params, "repository_id"), event_type: one(params, "event_type"),
      actor: one(params, "actor"), since: one(params, "since"), until: one(params, "until") };
    return { query, page: await getActivity(query) };
  });
  return <div className="page-stack"><PageHeading title="Activity" description="Actual authenticated GitHub webhook deliveries. REST commits remain commits." action={<RefreshButton />} />
    <form className="grid gap-3 sm:grid-cols-3" action="/activity">
      {(["repository_id", "event_type", "actor", "since", "until"] as const).map(key => <label key={key} className="text-sm">{key.replaceAll("_", " ")}<input className="block w-full rounded border border-[var(--border)] bg-[var(--surface)] p-2" name={key} defaultValue={result.ok ? result.data.query[key] ?? "" : ""} placeholder={key === "since" || key === "until" ? "ISO date with timezone" : undefined} /></label>)}
      <button className="button" type="submit">Apply filters</button>
    </form>
    {!result.ok ? <ApiState kind={result.error} /> : <>{result.data.page.items.length === 0 ? <EmptyState title="No captured activity" description="Permanent activity begins when webhook delivery is enabled and its worker processes deliveries. Historical commits are not push events. Filters may also exclude captured activity." /> : <ul className="divide-y divide-[var(--border)]">{result.data.page.items.map(event => <li key={event.id} className="flex flex-wrap justify-between gap-3 py-4"><div><strong>{event.event_type}</strong> {event.event_action ?? ""}<p className="muted text-sm">{event.actor_login ?? "Unknown actor"} · {event.event_at}</p>{event.repository_id && <Link className="accent text-sm" href={`/repositories/${event.repository_id}`}>Repository</Link>}</div><span className="muted text-sm">{event.processing_status}</span></li>)}</ul>}<Pagination path="/activity" data={result.data.page} query={result.data.query} /></>}
  </div>;
}
