import Link from "next/link";
import {
  ArrowRight,
  CalendarDays,
  CircleAlert,
  FolderGit2,
  GitPullRequest,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import {
  activityFor,
  findings,
  getPullRequest,
  getReview,
  repositories,
  repoFindings,
  reviews,
  risk,
  statistics,
} from "@/lib/mock-data";
import {
  Badge,
  Card,
  PageHeading,
  SeverityBadge,
  StatCard,
  StatusBadge,
} from "@/components/ui";
import {
  ActivityChart,
  SeverityChart,
} from "@/components/charts/review-charts";
import { ReviewList } from "@/components/reviews/review-list";
export function Dashboard() {
  return (
    <div className="page-stack">
      <PageHeading
        title="CodeReview AI"
        eyebrow="WORKSPACE OVERVIEW"
        description="Intelligent Pull Request Analysis"
        action={
          <div className="button text-xs muted">
            <CalendarDays size={14} /> Sep 3 - 9, 2026
          </div>
        }
      />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="muted text-sm">Your code quality, at a glance.</p>
        <Link
          href="/reviews"
          className="accent flex items-center gap-2 text-xs"
        >
          Explore reviews <ArrowRight size={14} />
        </Link>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Connected repositories"
          value={statistics.repositories}
          detail={`${repositories.length} repositories in workspace`}
          icon={<FolderGit2 size={17} />}
        />
        <StatCard
          label="Pull requests reviewed"
          value={statistics.reviewedPullRequests}
          detail="Unique PRs with completed reviews"
          icon={<GitPullRequest size={17} />}
        />
        <StatCard
          label="Total findings"
          value={statistics.findings}
          detail="Across all completed reviews"
          icon={<ShieldCheck size={17} />}
        />
        <StatCard
          label="High-severity findings"
          value={statistics.highSeverityFindings}
          detail="Require attention before merging"
          icon={<ShieldAlert size={17} />}
          tone="text-[var(--red)]"
        />
      </div>
      <div className="grid gap-5 lg:grid-cols-[1.7fr_1fr]">
        <Card>
          <div className="panel-head">
            <div>
              <h2>Review activity</h2>
              <p className="muted mt-1 text-xs">
                Completed reviews and findings over the last 7 days
              </p>
            </div>
            <Badge>7 days</Badge>
          </div>
          <div className="p-4">
            <ActivityChart data={activityFor()} />
          </div>
        </Card>
        <Card>
          <div className="panel-head">
            <h2>Findings by severity</h2>
            <Badge>{findings.length} findings</Badge>
          </div>
          <div className="p-4">
            <SeverityChart findings={findings} />
          </div>
        </Card>
      </div>
      <Card>
        <div className="panel-head">
          <h2>Recent reviews</h2>
          <Link
            className="accent flex items-center gap-2 text-xs"
            href="/reviews"
          >
            View all <ArrowRight size={13} />
          </Link>
        </div>
        <ReviewList
          items={[...reviews]
            .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
            .slice(0, 4)}
        />
      </Card>
      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <div className="panel-head">
            <h2>Repository health</h2>
            <Link className="accent text-xs" href="/repositories">
              All repositories
            </Link>
          </div>
          {repositories.map((r) => (
            <Link
              className="row row-link flex flex-wrap items-center justify-between gap-3"
              key={r.id}
              href={`/repositories/${r.id}`}
            >
              <div className="flex min-w-0 items-center gap-3">
                <FolderGit2 size={17} className="muted" />
                <div className="break-safe">
                  <p className="text-sm font-medium">
                    {r.owner}/{r.name}
                  </p>
                  <p className="muted mt-1 text-xs">
                    {r.language} · {repoFindings(r.id).length} findings
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                <StatusBadge status={r.isActive ? "active" : "inactive"} />
                <SeverityBadge severity={risk(repoFindings(r.id))} />
              </div>
            </Link>
          ))}
        </Card>
        <Card>
          <div className="panel-head">
            <h2 className="flex items-center gap-2">
              <CircleAlert size={15} className="text-[var(--red)]" /> Needs
              attention
            </h2>
            <Badge tone="high">High severity</Badge>
          </div>
          {findings
            .filter((f) => f.severity === "high")
            .map((f) => {
              const r = getReview(f.reviewId);
              const p = r && getPullRequest(r.pullRequestId);
              return (
                <Link
                  key={f.id}
                  className="row row-link block"
                  href={`/reviews/${f.reviewId}#${f.id}`}
                >
                  <p className="text-sm font-medium">{f.title}</p>
                  <p className="muted mt-2 break-all font-mono text-[11px]">
                    {f.file}:{f.startLine}
                  </p>
                  <div className="mt-3 flex items-center gap-2">
                    <Badge tone="high">High</Badge>
                    <span className="muted text-xs">
                      {f.category} · PR #{p?.number}
                    </span>
                    <ArrowRight size={13} className="muted ml-auto" />
                  </div>
                </Link>
              );
            })}
        </Card>
      </div>
    </div>
  );
}
