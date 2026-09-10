import { notFound } from "next/navigation";
import { FolderGit2, GitPullRequest } from "lucide-react";
import type { SearchParams } from "@/types/api";
import {
  getRepository,
  getRepositoryPullRequests,
} from "@/lib/api/repositories";
import { load } from "@/lib/api/server";
import { isUuid } from "@/lib/api/parsers";
import { paginationQuery, statusQuery } from "@/lib/api/filters";
import {
  Badge,
  Breadcrumbs,
  Card,
  PageHeading,
  StatCard,
  StatusBadge,
} from "@/components/ui";
import { ApiState } from "@/components/ui/api-state";
import { RefreshButton } from "@/components/ui/refresh-button";
import { GitHubLink } from "@/components/ui/github-link";
import { Filters } from "@/components/ui/filters";
import { Pagination } from "@/components/ui/pagination";
import { PullRequestList } from "@/components/pull-requests/pull-request-list";
import { formatDate } from "@/lib/utils";
export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<SearchParams>;
}) {
  const { id } = await params;
  if (!isUuid(id)) notFound();
  const filters = await searchParams;
  const result = await load(async () => {
    const query = { ...paginationQuery(filters), status: statusQuery(filters) };
    const repository = await getRepository(id);
    const page = await getRepositoryPullRequests(id, query);
    return { repository, page, query };
  });
  if (!result.ok) {
    if (result.error === "not_found") notFound();
    return <ApiState kind={result.error} />;
  }
  const { repository: r, page, query } = result.data,
    path = `/repositories/${id}`;
  return (
    <div className="page-stack">
      <Breadcrumbs
        items={[
          { label: "Repositories", href: "/repositories" },
          { label: r.full_name },
        ]}
      />
      <PageHeading
        title={r.full_name}
        description={r.description ?? "No description provided."}
        action={<RefreshButton />}
      />
      <div className="flex flex-wrap items-center gap-3">
        <StatusBadge status={r.is_active ? "active" : "inactive"} />
        <Badge>
          {r.is_private === null
            ? "Visibility unknown"
            : r.is_private
              ? "Private"
              : "Public"}
        </Badge>
        <GitHubLink url={r.html_url} />
      </div>
      <dl className="grid gap-4 border-y border-[var(--border)] py-5 sm:grid-cols-3">
        {[
          { label: "Default branch", value: r.default_branch },
          {
            label: "Primary language",
            value: r.primary_language ?? "Not available",
          },
          {
            label: "Last synchronized",
            value: formatDate(r.last_synced_at, "Never"),
          },
        ].map((item) => (
          <div key={item.label}>
            <dt className="muted text-xs">{item.label}</dt>
            <dd className="break-safe mt-1 text-sm">{item.value}</dd>
          </div>
        ))}
      </dl>
      <div className="grid gap-4 sm:grid-cols-2">
        <StatCard
          label="Pull Requests"
          value={r.pull_request_count}
          detail="Synchronized from GitHub"
          icon={<FolderGit2 size={17} />}
        />
        <StatCard
          label="Open Pull Requests"
          value={r.open_pull_request_count}
          detail="Currently open on GitHub"
          icon={<GitPullRequest size={17} />}
        />
      </div>
      <Filters path={path} values={query} mode="nested" />
      <Card>
        <div className="panel-head">
          <h2>Pull Requests</h2>
        </div>
        <PullRequestList items={page.items} repository />
      </Card>
      <Pagination path={path} data={page} query={query} />
    </div>
  );
}
