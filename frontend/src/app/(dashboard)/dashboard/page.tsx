import Link from "next/link";
import {
  FolderGit2,
  GitPullRequest,
  ShieldCheck,
  CircleAlert,
  GitMerge,
  GitPullRequestClosed,
} from "lucide-react";
import { loadDashboard } from "@/lib/api/server";
import { ApiState } from "@/components/ui/api-state";
import { Card, EmptyState, PageHeading, StatCard } from "@/components/ui";
import { RefreshButton } from "@/components/ui/refresh-button";
import { PullRequestList } from "@/components/pull-requests/pull-request-list";
export default async function Page() {
  const result = await loadDashboard();
  if (!result.ok)
    return (
      <div className="page-stack">
        <PageHeading
          title="CodeReview AI"
          description="Intelligent Pull Request Analysis"
        />
        <ApiState kind={result.error} />
      </div>
    );
  const d = result.data;
  return (
    <div className="page-stack">
      <PageHeading
        title="CodeReview AI"
        eyebrow="WORKSPACE OVERVIEW"
        description="Intelligent Pull Request Analysis"
        action={<RefreshButton />}
      />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Connected repositories"
          value={d.connected_repository_count}
          detail="Active repositories in PostgreSQL"
          icon={<FolderGit2 size={17} />}
        />
        <StatCard
          label="Total Pull Requests"
          value={d.total_pull_request_count}
          detail="Synchronized from GitHub"
          icon={<GitPullRequest size={17} />}
        />
        <StatCard
          label="Open Pull Requests"
          value={d.open_pr_count}
          detail="Awaiting merge or closure"
          icon={<GitPullRequest size={17} />}
        />
        <StatCard
          label="Closed Pull Requests"
          value={d.closed_pr_count}
          detail="Closed without merging"
          icon={<GitPullRequestClosed size={17} />}
        />
        <StatCard
          label="Merged Pull Requests"
          value={d.merged_pr_count}
          detail="Merged on GitHub"
          icon={<GitMerge size={17} />}
        />
        <StatCard
          label="Review attempts"
          value={d.total_reviews}
          detail="Automated static analysis"
          icon={<ShieldCheck size={17} />}
        />
        <StatCard
          label="Completed"
          value={d.completed_reviews}
          detail="Finished review attempts"
          icon={<CircleAlert size={17} />}
        />
        <StatCard
          label="Failed"
          value={d.failed_reviews}
          detail="Safe failure details available"
          icon={<CircleAlert size={17} />}
        />
      </div>
      <Card>
        <div className="panel-head">
          <h2>Recently updated Pull Requests</h2>
          <Link
            className="accent text-xs"
            href="/pull-requests"
            prefetch={false}
          >
            All pull requests
          </Link>
        </div>
        <PullRequestList items={d.recently_updated_pull_requests} />
      </Card>
      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <div className="panel-head">
            <h2>Pull Request status</h2>
          </div>
          {d.total_pull_request_count === 0 ? (
            <EmptyState
              title="No Pull Request activity yet"
              description="Status distribution will appear when real Pull Requests are synchronized."
            />
          ) : (
            <dl className="space-y-4 p-5">
              {[
                { name: "Open", count: d.open_pr_count },
                { name: "Closed", count: d.closed_pr_count },
                { name: "Merged", count: d.merged_pr_count },
              ].map((item) => (
                <div key={item.name}>
                  <div className="mb-2 flex justify-between">
                    <dt>{item.name}</dt>
                    <dd>{item.count}</dd>
                  </div>
                  <meter
                    min={0}
                    max={d.total_pull_request_count}
                    value={item.count}
                    aria-label={`${item.name} pull requests`}
                    className="w-full"
                  />
                </div>
              ))}
            </dl>
          )}
        </Card>
        <Card>
          <div className="panel-head">
            <h2>Static review results</h2>
            <Link
              className="accent text-xs"
              href="/reviews"
              prefetch={false}
            >
              All review attempts
            </Link>
          </div>
          {d.total_reviews === 0 ? (
            <EmptyState
              title="No static review attempts yet"
              description="Run the protected review CLI for a synchronized Pull Request to create results."
            />
          ) : (
            <dl className="grid gap-4 p-5 sm:grid-cols-2">
              {[
                { name: "In progress", count: d.in_progress_reviews },
                { name: "Findings", count: d.total_findings },
                {
                  name: "High-severity findings",
                  count: d.high_severity_findings,
                },
                { name: "AI analysis", count: "Not enabled" },
              ].map((item) => (
                <div key={item.name} className="bordered rounded-md p-3">
                  <dt className="muted text-xs">{item.name}</dt>
                  <dd className="mt-1 font-semibold">{item.count}</dd>
                </div>
              ))}
            </dl>
          )}
        </Card>
      </div>
    </div>
  );
}
