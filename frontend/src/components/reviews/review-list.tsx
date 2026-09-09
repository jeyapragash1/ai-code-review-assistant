import Link from "next/link";
import { ArrowUpRight, GitPullRequest } from "lucide-react";
import {
  getPullRequest,
  getRepository,
  reviewFindings,
  reviewRisk,
} from "@/lib/mock-data";
import { formatDate } from "@/lib/utils";
import { EmptyState, SeverityBadge, StatusBadge, Table } from "@/components/ui";
import type { Review } from "@/types";
export function ReviewList({ items }: { items: Review[] }) {
  if (!items.length)
    return (
      <EmptyState
        title="No reviews yet"
        description="Reviews will appear here when available."
      />
    );
  return (
    <>
      <div className="hidden lg:block">
        <Table>
          <thead>
            <tr>
              <th>Pull request</th>
              <th>Status</th>
              <th>Risk</th>
              <th>Findings</th>
              <th>Duration</th>
              <th>Reviewed</th>
              <th>
                <span className="sr-only">Details</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {items.map((r) => {
              const p = getPullRequest(r.pullRequestId);
              const repo = p && getRepository(p.repositoryId);
              if (!p || !repo) return null;
              return (
                <tr key={r.id}>
                  <td>
                    <Link
                      href={`/reviews/${r.id}`}
                      className="font-medium hover:underline"
                    >
                      {p.title}
                    </Link>
                    <p className="muted mt-1 text-xs">
                      {repo.owner}/{repo.name} <span className="mx-1">/</span> #
                      {p.number}
                    </p>
                  </td>
                  <td>
                    <StatusBadge status={r.status} />
                  </td>
                  <td>
                    <SeverityBadge severity={reviewRisk(r)} />
                  </td>
                  <td>{reviewFindings(r.id).length}</td>
                  <td className="muted">
                    {r.status === "completed"
                      ? `${(r.staticSeconds + r.aiSeconds).toFixed(1)}s`
                      : "--"}
                  </td>
                  <td className="muted whitespace-nowrap">
                    {formatDate(r.createdAt)}
                  </td>
                  <td>
                    <Link
                      href={`/reviews/${r.id}`}
                      aria-label={`Open review ${r.id}`}
                    >
                      <ArrowUpRight size={16} />
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </Table>
      </div>
      <div className="lg:hidden">
        {items.map((r) => {
          const p = getPullRequest(r.pullRequestId);
          const repo = p && getRepository(p.repositoryId);
          if (!p || !repo) return null;
          return (
            <Link
              key={r.id}
              href={`/reviews/${r.id}`}
              className="row row-link block"
            >
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <GitPullRequest size={14} className="accent" />
                <span className="muted text-xs">
                  {repo.name} #{p.number}
                </span>
                <StatusBadge status={r.status} />
              </div>
              <h3 className="text-sm font-medium">{p.title}</h3>
              <div className="mt-3 flex flex-wrap items-center gap-3">
                <SeverityBadge severity={reviewRisk(r)} />
                <span className="muted text-xs">
                  {reviewFindings(r.id).length} findings ·{" "}
                  {formatDate(r.createdAt)}
                </span>
              </div>
              <p className="muted mt-2 text-xs">
                {r.status === "completed"
                  ? `${(r.staticSeconds + r.aiSeconds).toFixed(1)}s processing time`
                  : "Duration pending"}
              </p>
            </Link>
          );
        })}
      </div>
    </>
  );
}
