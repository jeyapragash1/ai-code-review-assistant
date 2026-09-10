import { notFound } from "next/navigation";
import { FileCode, GitCommitHorizontal } from "lucide-react";
import { getPullRequest } from "@/lib/api/pull-requests";
import { load } from "@/lib/api/server";
import { isUuid } from "@/lib/api/parsers";
import {
  Badge,
  Breadcrumbs,
  Card,
  EmptyState,
  PageHeading,
  StatCard,
  StatusBadge,
} from "@/components/ui";
import { ApiState } from "@/components/ui/api-state";
import { GitHubLink } from "@/components/ui/github-link";
import { RefreshButton } from "@/components/ui/refresh-button";
import { formatDate, shortSha } from "@/lib/utils";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  if (!isUuid(id)) notFound();
  const result = await load(() => getPullRequest(id));
  if (!result.ok) {
    if (result.error === "not_found") notFound();
    return <ApiState kind={result.error} />;
  }
  const p = result.data;
  return (
    <div className="page-stack">
      <Breadcrumbs
        items={[
          { label: "Pull Requests", href: "/pull-requests" },
          {
            label: p.repository.full_name,
            href: `/repositories/${p.repository_id}`,
          },
          { label: `#${p.github_pr_number}` },
        ]}
      />
      <PageHeading
        title={`${p.title} #${p.github_pr_number}`}
        description={`${p.repository.full_name} · by ${p.author_login}`}
        action={<RefreshButton />}
      />
      <div className="flex flex-wrap items-center gap-3">
        <StatusBadge status={p.status} />
        <Badge>
          {p.is_draft === null
            ? "Draft state unavailable"
            : p.is_draft
              ? "Draft"
              : "Ready for review"}
        </Badge>
        <span
          title={p.head_sha}
          aria-label={`Commit ${p.head_sha}`}
          className="flex items-center gap-1 font-mono text-xs"
        >
          <GitCommitHorizontal size={14} />
          {shortSha(p.head_sha)}
        </span>
        <GitHubLink url={p.html_url} />
      </div>
      <dl className="grid gap-4 border-y border-[var(--border)] py-5 sm:grid-cols-2 lg:grid-cols-3">
        {[
          { label: "Head branch", value: p.head_branch },
          { label: "Base branch", value: p.base_branch },
          {
            label: "Created on GitHub",
            value: formatDate(p.github_created_at),
          },
          {
            label: "Updated on GitHub",
            value: formatDate(p.github_updated_at),
          },
          {
            label: "Last synchronized",
            value: formatDate(p.last_synced_at, "Never"),
          },
        ].map((item) => (
          <div key={item.label}>
            <dt className="muted text-xs">{item.label}</dt>
            <dd className="break-safe mt-1">{item.value}</dd>
          </div>
        ))}
      </dl>
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="Changed files"
          value={p.changed_files ?? "Not available"}
          detail="From GitHub PR details"
          icon={<FileCode size={17} />}
        />
        <StatCard
          label="Additions"
          value={p.additions ?? "Not available"}
          detail="Lines added"
          icon={<FileCode size={17} />}
        />
        <StatCard
          label="Deletions"
          value={p.deletions ?? "Not available"}
          detail="Lines removed"
          icon={<FileCode size={17} />}
        />
      </div>
      <Card>
        <EmptyState
          title="AI review results are not available yet."
          description="AI review results will appear after the review engine processes this Pull Request."
        />
      </Card>
    </div>
  );
}
