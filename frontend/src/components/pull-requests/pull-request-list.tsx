import Link from "next/link";
import { GitBranch, GitPullRequest } from "lucide-react";
import type { PullRequest } from "@/types/pull-request";
import { formatDate } from "@/lib/utils";
import { Badge, EmptyState, StatusBadge } from "@/components/ui";
export function PullRequestList({
  items,
  repository = false,
}: {
  items: PullRequest[];
  repository?: boolean;
}) {
  if (!items.length)
    return (
      <EmptyState
        title={
          repository
            ? "No Pull Requests have been synchronized for this repository yet."
            : "No Pull Requests found."
        }
        description="Create or synchronize a GitHub Pull Request to see it here."
      />
    );
  return (
    <div>
      {items.map((p) => (
        <article
          key={p.id}
          className="row grid gap-3 lg:grid-cols-[minmax(0,1fr)_200px]"
        >
          <div className="min-w-0">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <GitPullRequest size={15} className="accent" />
              <Link
                href={`/repositories/${p.repository_id}`}
                className="muted break-safe text-xs"
                prefetch={false}
              >
                {p.repository_full_name}
              </Link>
              <StatusBadge status={p.status} />
              {p.is_draft && <Badge>Draft</Badge>}
            </div>
            <Link
              href={`/pull-requests/${p.id}`}
              className="break-safe font-semibold hover:underline"
              prefetch={false}
            >
              {p.title} #{p.github_pr_number}
            </Link>
            <p className="muted mt-2 text-xs">by {p.author_login}</p>
            <p className="muted mt-2 flex items-start gap-1 break-all text-xs">
              <GitBranch size={13} className="shrink-0" />
              {p.head_branch} → {p.base_branch}
            </p>
          </div>
          <div className="muted space-y-2 text-xs">
            <p>{p.changed_files ?? "Unknown"} changed files</p>
            <p>Updated {formatDate(p.github_updated_at)}</p>
            <p>Synced {formatDate(p.last_synced_at, "Never")}</p>
          </div>
        </article>
      ))}
    </div>
  );
}
