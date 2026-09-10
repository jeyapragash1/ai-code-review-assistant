import type { SearchParams } from "@/types/api";
import { load } from "@/lib/api/server";
import { getPullRequests } from "@/lib/api/pull-requests";
import { getRepositories } from "@/lib/api/repositories";
import {
  paginationQuery,
  repositoryQuery,
  searchQuery,
  statusQuery,
} from "@/lib/api/filters";
import { PullRequestList } from "@/components/pull-requests/pull-request-list";
import { ApiState } from "@/components/ui/api-state";
import { Filters } from "@/components/ui/filters";
import { Pagination } from "@/components/ui/pagination";
import { Card, PageHeading } from "@/components/ui";
import { RefreshButton } from "@/components/ui/refresh-button";
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;
  const result = await load(async () => {
    const query = {
      ...paginationQuery(params),
      search: searchQuery(params),
      repository_id: repositoryQuery(params),
      status: statusQuery(params),
    };
    const page = await getPullRequests(query);
    const first = await getRepositories({ page_size: 100 });
    const repositories = [...first.items];
    // Repository choices must cover the complete backend collection, not just page one.
    for (let page = 2; page <= first.total_pages; page++)
      repositories.push(
        ...(await getRepositories({ page, page_size: 100 })).items,
      );
    return { query, page, repositories };
  });
  return (
    <div className="page-stack">
      <PageHeading
        title="Pull Requests"
        description="Real changes synchronized from your GitHub repositories."
        action={<RefreshButton />}
      />
      {result.ok ? (
        <>
          <Filters
            path="/pull-requests"
            values={result.data.query}
            mode="pull-requests"
            repositories={result.data.repositories}
          />
          <Card>
            <PullRequestList items={result.data.page.items} />
          </Card>
          <Pagination
            path="/pull-requests"
            data={result.data.page}
            query={result.data.query}
          />
        </>
      ) : (
        <ApiState kind={result.error} />
      )}
    </div>
  );
}
