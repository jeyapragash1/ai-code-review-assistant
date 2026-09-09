import Link from "next/link";
import { GitBranch, GitPullRequest } from "lucide-react";
import type { PullRequest } from "@/types";
import {
  getRepository,
  prReviews,
  reviewFindings,
  reviewRisk,
} from "@/lib/mock-data";
import { formatDate } from "@/lib/utils";
import { EmptyState, SeverityBadge, StatusBadge } from "@/components/ui";
export function PullRequestList({ items }: { items: PullRequest[] }) {
  if (!items.length) return <EmptyState title="No pull requests" />;
  return (
    <div>
      {items.map((p) => {
        const repo = getRepository(p.repositoryId);
        const latest = prReviews(p.id)[0];
        return (
          <div
            key={p.id}
            className="row row-link grid gap-4 lg:grid-cols-[minmax(0,1fr)_220px]"
          >
            <div className="min-w-0">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <GitPullRequest size={15} className="accent" />
                <Link
                  href={`/repositories/${p.repositoryId}`}
                  className="muted text-xs hover:underline"
                >
                  {repo?.owner}/{repo?.name}
                </Link>
                <span className="muted text-xs">#{p.number}</span>
                <StatusBadge status={p.status} />
              </div>
              <Link
                href={`/pull-requests/${p.id}`}
                className="break-safe text-sm font-semibold hover:underline"
              >
                {p.title}
              </Link>
              <div className="muted mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
                <span>by {p.author}</span>
                <span className="flex min-w-0 items-center gap-1 break-all">
                  <GitBranch size={12} className="shrink-0" />
                  {p.headBranch} → {p.baseBranch}
                </span>
              </div>
            </div>
            <div className="flex flex-col justify-center gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <SeverityBadge
                  severity={latest ? reviewRisk(latest) : "pending"}
                />
                <span className="muted text-xs">
                  {latest ? reviewFindings(latest.id).length : 0} findings ·{" "}
                  {p.filesChanged} files
                </span>
              </div>
              <span className="muted text-xs">
                Latest review{" "}
                {latest ? formatDate(latest.createdAt) : "not available"}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
