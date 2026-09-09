import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowRight,
  FileCode,
  GitBranch,
  GitCommitHorizontal,
  ShieldCheck,
} from "lucide-react";
import {
  getPullRequest,
  getRepository,
  prReviews,
  reviewFindings,
  reviewRisk,
} from "@/lib/mock-data";
import { shortSha } from "@/lib/utils";
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
import { ReviewList } from "@/components/reviews/review-list";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const p = getPullRequest(id);
  if (!p) notFound();
  const repo = getRepository(p.repositoryId);
  if (!repo) notFound();
  const rs = prReviews(id);
  const latest = rs[0];
  const fs = latest ? reviewFindings(latest.id) : [];
  return (
    <div className="page-stack">
      <Breadcrumbs
        items={[
          { label: "Pull Requests", href: "/pull-requests" },
          { label: `${repo.name} #${p.number}` },
        ]}
      />
      <PageHeading
        title={`${p.title} #${p.number}`}
        description={`${repo.owner}/${repo.name} · opened by ${p.author}`}
        action={<GitHubLink query={`${repo.owner}/${repo.name}`} />}
      />
      <div className="flex flex-wrap items-center gap-3">
        <StatusBadge status={p.status} />
        <span className="muted flex items-center gap-1 break-all text-xs">
          <GitBranch size={13} />
          {p.headBranch} → {p.baseBranch}
        </span>
        <span
          className="muted flex items-center gap-1 font-mono text-xs"
          title={p.headSha}
          aria-label={`Commit ${p.headSha}`}
        >
          <GitCommitHorizontal size={14} />
          {shortSha(p.headSha)}
        </span>
        <Link href={`/repositories/${repo.id}`} className="accent text-xs">
          Repository details
        </Link>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Files changed"
          value={p.filesChanged}
          detail={`${p.additions} additions / ${p.deletions} deletions`}
          icon={<FileCode size={17} />}
        />
        <StatCard
          label="Lines added"
          value={`+${p.additions}`}
          detail={`${p.deletions} lines removed`}
          icon={<FileCode size={17} />}
          tone="text-[var(--green)]"
        />
        <StatCard
          label="Findings"
          value={fs.length}
          detail="From the latest review"
          icon={<ShieldCheck size={17} />}
        />
        <StatCard
          label="Reviews"
          value={rs.length}
          detail="Including previous commits"
          icon={<GitCommitHorizontal size={17} />}
        />
      </div>
      <Card>
        <div className="panel-head">
          <h2>Latest review summary</h2>
          {latest && (
            <div className="flex gap-2">
              <StatusBadge status={latest.status} />
              <SeverityBadge severity={reviewRisk(latest)} />
            </div>
          )}
        </div>
        <div className="space-y-4 p-5">
          <p className="muted leading-relaxed">
            {latest?.summary ?? "No review is available for this pull request."}
          </p>
          <RiskSummary findings={fs} />
          {latest && (
            <Link
              className="accent inline-flex items-center gap-2 text-xs"
              href={`/reviews/${latest.id}`}
            >
              View full review <ArrowRight size={13} />
            </Link>
          )}
        </div>
      </Card>
      <FindingList findings={fs} />
      <Card>
        <div className="panel-head">
          <h2>Review history</h2>
        </div>
        <ReviewList items={rs} />
      </Card>
    </div>
  );
}
