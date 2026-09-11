import Link from "next/link";
import { GitCommitHorizontal, GitPullRequest, ShieldCheck } from "lucide-react";
import type { Review } from "@/types/review";
import { formatDateTime, formatDuration, label, shortSha } from "@/lib/utils";
import { Badge, EmptyState, StatusBadge } from "@/components/ui";

function pullRequestLabel(review: Review) {
  if (review.pull_request_number && review.pull_request_title)
    return `${review.pull_request_title} #${review.pull_request_number}`;
  if (review.pull_request_number) return `Pull Request #${review.pull_request_number}`;
  return "Pull Request details";
}

export function ReviewList({
  items,
  emptyTitle = "No review attempts found.",
  emptyDescription = "Run the protected review CLI for a synchronized Pull Request to populate this view.",
}: {
  items: Review[];
  emptyTitle?: string;
  emptyDescription?: string;
}) {
  if (!items.length)
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  return (
    <div>
      {items.map((review) => (
        <article
          key={review.id}
          className="row grid gap-3 lg:grid-cols-[minmax(0,1fr)_230px]"
        >
          <div className="min-w-0">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <ShieldCheck size={15} className="accent" />
              {review.repository_full_name && (
                <span className="muted break-safe text-xs">
                  {review.repository_full_name}
                </span>
              )}
              <StatusBadge status={review.status} />
              {review.overall_risk && (
                <Badge tone={review.overall_risk}>
                  Risk: {label(review.overall_risk)}
                </Badge>
              )}
            </div>
            <Link
              href={`/reviews/${review.id}`}
              className="break-safe font-semibold hover:underline"
              prefetch={false}
            >
              Attempt {review.attempt_number} · {pullRequestLabel(review)}
            </Link>
            <div className="muted mt-2 flex flex-wrap items-center gap-3 text-xs">
              <span
                title={review.commit_sha}
                aria-label={`Commit ${review.commit_sha}`}
                className="flex items-center gap-1 font-mono"
              >
                <GitCommitHorizontal size={13} />
                {shortSha(review.commit_sha)}
              </span>
              <span>{label(review.trigger_type)} trigger</span>
              <span>{review.findings_count} findings</span>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <Link
                href={`/reviews/${review.id}`}
                className="button"
                prefetch={false}
              >
                Review detail
              </Link>
              <Link
                href={`/pull-requests/${review.pull_request_id}`}
                className="button"
                prefetch={false}
              >
                <GitPullRequest size={14} />
                Related PR
              </Link>
            </div>
          </div>
          <dl className="muted grid gap-2 text-xs sm:grid-cols-2 lg:block lg:space-y-2">
            <div>
              <dt>Started</dt>
              <dd>{formatDateTime(review.started_at)}</dd>
            </div>
            <div>
              <dt>Completed</dt>
              <dd>{formatDateTime(review.completed_at, "Not completed")}</dd>
            </div>
            <div>
              <dt>Duration</dt>
              <dd>{formatDuration(review.duration_ms)}</dd>
            </div>
          </dl>
        </article>
      ))}
    </div>
  );
}
