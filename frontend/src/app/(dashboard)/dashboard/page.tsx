import { AccountDashboard } from "@/components/dashboard/account-dashboard";
import { PageHeading, Card } from "@/components/ui";
import { RefreshButton } from "@/components/ui/refresh-button";
import { ApiState } from "@/components/ui/api-state";
import { PullRequestList } from "@/components/pull-requests/pull-request-list";
import { load } from "@/lib/api/server";
import { get } from "@/lib/api/client";
import { one } from "@/lib/api/filters";
import { parsePage, parsePullRequest } from "@/lib/api/parsers";
import type { SearchParams } from "@/types/api";

export default async function Page({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const filters = await searchParams;
  const recent = await load(() => get(["pull-requests"], value => parsePage(value, parsePullRequest),
    { repository_id: one(filters, "repository_id"), page_size: 5 }));
  return <div className="page-stack">
    <PageHeading title="CodeReview AI" eyebrow="ACCOUNT OVERVIEW" description="Authorized GitHub repositories, activity and static reviews." action={<RefreshButton />} />
    <AccountDashboard filters={filters} />
    <Card><div className="panel-head"><h2>Recently updated Pull Requests</h2></div>
      {recent.ok ? <PullRequestList items={recent.data.items} /> : <ApiState kind={recent.error} />}
    </Card>
  </div>;
}
