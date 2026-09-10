import type { SearchParams } from "@/types/api";
import { load } from "@/lib/api/server";
import { getRepositories } from "@/lib/api/repositories";
import { activeQuery, paginationQuery, searchQuery } from "@/lib/api/filters";
import { RepositoryList } from "@/components/repositories/repository-list";
import { Filters } from "@/components/ui/filters";
import { Pagination } from "@/components/ui/pagination";
import { ApiState } from "@/components/ui/api-state";
import { PageHeading } from "@/components/ui";
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
      is_active: activeQuery(params),
    };
    return { query, page: await getRepositories(query) };
  });
  return (
    <div className="page-stack">
      <PageHeading
        title="Repositories"
        description="Repository metadata synchronized from GitHub."
        action={<RefreshButton />}
      />
      {result.ok ? (
        <>
          <Filters
            path="/repositories"
            values={result.data.query}
            mode="repositories"
          />
          <RepositoryList items={result.data.page.items} />
          <Pagination
            path="/repositories"
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
