import type { SearchParams } from "@/types/api";
import {
  commitShaQuery,
  paginationQuery,
  pullRequestQuery,
  repositoryQuery,
  reviewRiskQuery,
  reviewStatusQuery,
} from "@/lib/api/filters";
import { getReviews } from "@/lib/api/reviews";
import { load } from "@/lib/api/server";
import { ApiState } from "@/components/ui/api-state";
import { Pagination } from "@/components/ui/pagination";
import { RefreshButton } from "@/components/ui/refresh-button";
import { REVIEW_RISKS, REVIEW_STATUSES } from "@/types/review";
import { Button, Card, Input, PageHeading, Select } from "@/components/ui";
import { ReviewList } from "@/components/reviews/review-list";
import { label } from "@/lib/utils";

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;
  const result = await load(async () => {
    const query = {
      ...paginationQuery(params),
      pull_request_id: pullRequestQuery(params),
      repository_id: repositoryQuery(params),
      status: reviewStatusQuery(params),
      overall_risk: reviewRiskQuery(params),
      commit_sha: commitShaQuery(params),
    };
    const [page, unfiltered] = await Promise.all([
      getReviews(query),
      getReviews({ page: 1, page_size: 1 }),
    ]);
    return { query, page, unfilteredTotal: unfiltered.total };
  });
  return (
    <div className="page-stack">
      <PageHeading
        title="Reviews"
        description="Real static-analysis review attempts persisted by the backend."
        action={<RefreshButton />}
      />
      {result.ok ? (
        <>
          <form
            method="get"
            action="/reviews"
            className="flex flex-wrap items-end gap-3"
          >
            <input type="hidden" name="page" value="1" />
            {result.data.query.pull_request_id && (
              <input
                type="hidden"
                name="pull_request_id"
                value={result.data.query.pull_request_id}
              />
            )}
            {result.data.query.repository_id && (
              <input
                type="hidden"
                name="repository_id"
                value={result.data.query.repository_id}
              />
            )}
            <Select
              label="Status"
              name="status"
              defaultValue={String(result.data.query.status ?? "")}
            >
              <option value="">All statuses</option>
              {REVIEW_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {label(status)}
                </option>
              ))}
            </Select>
            <Select
              label="Overall risk"
              name="overall_risk"
              defaultValue={String(result.data.query.overall_risk ?? "")}
            >
              <option value="">All risks</option>
              {REVIEW_RISKS.map((risk) => (
                <option key={risk} value={risk}>
                  {label(risk)}
                </option>
              ))}
            </Select>
            <div className="min-w-0 flex-[1_1_220px]">
              <Input
                label="Commit SHA"
                name="commit_sha"
                minLength={7}
                maxLength={40}
                defaultValue={String(result.data.query.commit_sha ?? "")}
                placeholder="abcdef1"
              />
            </div>
            <div className="w-24">
              <Input
                label="Page size"
                name="page_size"
                type="number"
                min={1}
                max={100}
                required
                defaultValue={String(result.data.query.page_size ?? 20)}
              />
            </div>
            <Button type="submit" className="primary">
              Apply
            </Button>
            <a className="button" href="/reviews">
              Clear
            </a>
          </form>
          <Card>
            <ReviewList
              items={result.data.page.items}
              emptyTitle={
                result.data.unfilteredTotal === 0
                  ? "No review attempts found."
                  : "No review attempts match these filters."
              }
              emptyDescription={
                result.data.unfilteredTotal === 0
                  ? "Run the protected review CLI for a synchronized Pull Request to populate this view."
                  : "Clear filters or adjust the status, risk, or commit SHA."
              }
            />
          </Card>
          <Pagination
            path="/reviews"
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
