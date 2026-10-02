import type { SearchParams } from "@/types/api";
import { load } from "@/lib/api/server";
import { getCommits } from "@/lib/api/commits";
import { paginationQuery, one } from "@/lib/api/filters";
import { CommitList } from "@/components/commits/commit-list";
import { ApiState } from "@/components/ui/api-state";
import { PageHeading } from "@/components/ui";
import { Pagination } from "@/components/ui/pagination";
import { RefreshButton } from "@/components/ui/refresh-button";

export default async function Page({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const params = await searchParams;
  const result = await load(async () => { const query = { ...paginationQuery(params), repository_id: one(params, "repository_id") }; return { query, page: await getCommits(query) }; });
  return <div className="page-stack"><PageHeading title="Commits" description="Metadata-only commits synchronized from GitHub. Commits are not represented as push events." action={<RefreshButton />} />{result.ok ? <><CommitList items={result.data.page.items} /><Pagination path="/commits" data={result.data.page} query={result.data.query} /></> : <ApiState kind={result.error} />}</div>;
}