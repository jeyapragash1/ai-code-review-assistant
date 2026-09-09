import { notFound } from "next/navigation";
import {
  FolderGit2,
  GitBranch,
  GitPullRequest,
  ShieldAlert,
} from "lucide-react";
import {
  activityFor,
  getRepository,
  repoFindings,
  repoPRs,
  repoReviews,
  risk,
} from "@/lib/mock-data";
import {
  Badge,
  Breadcrumbs,
  Card,
  PageHeading,
  SeverityBadge,
  StatCard,
  StatusBadge,
} from "@/components/ui";
import { GitHubLink } from "@/components/ui/github-link";
import { PullRequestList } from "@/components/pull-requests/pull-request-list";
import { FindingList } from "@/components/findings/finding-list";
import { ActivityChart } from "@/components/charts/review-charts";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const repo = getRepository(id);
  if (!repo) notFound();
  const prs = repoPRs(id);
  const rs = repoReviews(id);
  const fs = repoFindings(id);
  return (
    <div className="page-stack">
      <Breadcrumbs
        items={[
          { label: "Repositories", href: "/repositories" },
          { label: repo.name },
        ]}
      />
      <PageHeading
        title={`${repo.owner}/${repo.name}`}
        description={repo.description}
        action={<GitHubLink query={`${repo.owner}/${repo.name}`} />}
      />
      <div className="flex flex-wrap items-center gap-3">
        <StatusBadge status={repo.isActive ? "active" : "inactive"} />
        <Badge>{repo.language}</Badge>
        <span className="muted flex items-center gap-1 text-xs">
          <GitBranch size={13} />
          {repo.defaultBranch}
        </span>
        <SeverityBadge severity={risk(fs)} />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Pull requests"
          value={prs.length}
          detail="Tracked in this repository"
          icon={<GitPullRequest size={17} />}
        />
        <StatCard
          label="PRs reviewed"
          value={
            new Set(
              rs
                .filter((r) => r.status === "completed")
                .map((r) => r.pullRequestId),
            ).size
          }
          detail="With completed analysis"
          icon={<FolderGit2 size={17} />}
        />
        <StatCard
          label="Total findings"
          value={fs.length}
          detail="Across stored reviews"
          icon={<ShieldAlert size={17} />}
        />
        <StatCard
          label="High severity"
          value={fs.filter((f) => f.severity === "high").length}
          detail="Require human verification"
          icon={<ShieldAlert size={17} />}
        />
      </div>
      <Card>
        <div className="panel-head">
          <h2>Review activity</h2>
          <span className="muted text-xs">Sep 3 - 9, 2026</span>
        </div>
        <div className="p-5">
          <ActivityChart data={activityFor(rs)} />
        </div>
      </Card>
      <Card>
        <div className="panel-head">
          <h2>Recent pull requests</h2>
        </div>
        <PullRequestList items={prs} />
      </Card>
      <FindingList findings={fs} />
    </div>
  );
}
