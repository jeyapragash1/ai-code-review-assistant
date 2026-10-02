import type { SearchParams } from "@/types/api";
import { load } from "@/lib/api/server";
import { getIssues } from "@/lib/api/issues";
import { paginationQuery, one } from "@/lib/api/filters";
import { IssueList } from "@/components/issues/issue-list";
import { ApiState } from "@/components/ui/api-state";
import { PageHeading } from "@/components/ui";
import { Pagination } from "@/components/ui/pagination";
import { RefreshButton } from "@/components/ui/refresh-button";

export default async function Page({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const params = await searchParams;
  const result = await load(async () => {
    const query = { ...paginationQuery(params), state: one(params, "state") as "open" | "closed" | undefined, search: one(params, "search"), author: one(params, "author"), assignee: one(params, "assignee"), label: one(params, "label") };
    return { query, page: await getIssues(query) };
  });
  return <div className="page-stack"><PageHeading title="Issues" description="Real GitHub issues synchronized without double-counting Pull Requests." action={<RefreshButton />} />{result.ok ? <><IssueList items={result.data.page.items} /><Pagination path="/issues" data={result.data.page} query={result.data.query} /></> : <ApiState kind={result.error} />}</div>;
}
