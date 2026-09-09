import Link from "next/link";
import { notFound } from "next/navigation";
import {
  Clock3,
  FileSearch,
  GitCommitHorizontal,
  Info,
  Sparkles,
} from "lucide-react";
import {
  getPullRequest,
  getRepository,
  getReview,
  reviewFindings,
  reviewRisk,
} from "@/lib/mock-data";
import { formatDate, shortSha } from "@/lib/utils";
import {
  Breadcrumbs,
  Card,
  PageHeading,
  RiskSummary,
  SeverityBadge,
  StatCard,
  StatusBadge,
} from "@/components/ui";
import { GitHubLink } from "@/components/ui/github-link";
import { FindingList } from "@/components/findings/finding-list";
import { SeverityChart } from "@/components/charts/review-charts";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const r = getReview(id);
  if (!r) notFound();
  const p = getPullRequest(r.pullRequestId);
  if (!p) notFound();
  const repo = getRepository(p.repositoryId);
  if (!repo) notFound();
  const fs = reviewFindings(id);
  return (
    <div className="page-stack">
      <Breadcrumbs
        items={[
          { label: "Reviews", href: "/reviews" },
          { label: id.toUpperCase() },
        ]}
      />
      <PageHeading
        title={p.title}
        eyebrow={`REVIEW ${id.toUpperCase()} / ${formatDate(r.createdAt)}`}
        description={`${repo.owner}/${repo.name} · Pull request #${p.number}`}
        action={<GitHubLink query={`${repo.owner}/${repo.name}`} />}
      />
      <div className="flex flex-wrap items-center gap-3">
        <StatusBadge status={r.status} />
        <SeverityBadge severity={reviewRisk(r)} />
        <Link className="accent text-xs" href={`/pull-requests/${p.id}`}>
          PR #{p.number}
        </Link>
        <Link className="accent text-xs" href={`/repositories/${repo.id}`}>
          {repo.name}
        </Link>
        <span
          className="muted flex items-center gap-1 font-mono text-xs"
          title={r.commitSha}
          aria-label={`Commit ${r.commitSha}`}
        >
          <GitCommitHorizontal size={14} />
          {shortSha(r.commitSha)}
        </span>
        <span className="muted text-xs">by {p.author}</span>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total findings"
          value={fs.length}
          detail={
            r.status === "completed"
              ? "Analysis complete"
              : "Analysis incomplete"
          }
          icon={<FileSearch size={17} />}
        />
        <StatCard
          label="Processing time"
          value={
            r.status === "completed"
              ? `${(r.staticSeconds + r.aiSeconds).toFixed(1)}s`
              : "--"
          }
          detail="Static and AI analysis combined"
          icon={<Clock3 size={17} />}
        />
        <StatCard
          label="Static analysis"
          value={`${r.staticSeconds.toFixed(1)}s`}
          detail="Rules and pattern checks"
          icon={<FileSearch size={17} />}
        />
        <StatCard
          label="AI analysis"
          value={r.status === "completed" ? `${r.aiSeconds.toFixed(1)}s` : "--"}
          detail="Contextual code review"
          icon={<Sparkles size={17} />}
        />
      </div>
      <div className="grid gap-5 lg:grid-cols-[1.7fr_1fr]">
        <Card>
          <div className="panel-head">
            <h2 className="flex items-center gap-2">
              <Sparkles size={15} className="accent" /> Review summary
            </h2>
          </div>
          <div className="space-y-5 p-5">
            <p className="text-sm leading-7">{r.summary}</p>
            <RiskSummary findings={fs} />
            <div className="flex items-start gap-3 border-t border-[var(--border)] pt-5">
              <Info size={17} className="accent mt-0.5 shrink-0" />
              <p className="muted text-xs leading-relaxed">
                AI findings are suggestions, not a guarantee of correctness. A
                human must verify every finding and proposed change before
                merging.
              </p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="panel-head">
            <h2>Severity distribution</h2>
          </div>
          <div className="px-4 pb-5">
            <SeverityChart findings={fs} />
          </div>
        </Card>
      </div>
      {r.status === "completed" ? (
        <FindingList findings={fs} />
      ) : (
        <div className="bordered rounded-md p-5">
          <h2 className="font-semibold">
            {r.status === "failed"
              ? "Review could not be completed"
              : "Review in progress"}
          </h2>
          <p className="muted mt-2 text-sm">
            This is a fixed demo snapshot. No background processing or retry is
            running.
          </p>
        </div>
      )}
    </div>
  );
}
