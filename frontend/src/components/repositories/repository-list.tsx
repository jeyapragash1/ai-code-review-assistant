import Link from "next/link";
import { FolderGit2, GitBranch } from "lucide-react";
import type { Repository } from "@/types/repository";
import { formatDate } from "@/lib/utils";
import { Badge, Card, EmptyState, StatusBadge } from "@/components/ui";
import { GitHubLink } from "@/components/ui/github-link";
export function RepositoryList({ items }: { items: Repository[] }) {
  if (!items.length)
    return (
      <EmptyState
        title="No repositories found."
        description="Adjust your filters or run the backend synchronization CLI to add real repository data."
      />
    );
  return (
    <div className="grid gap-5 lg:grid-cols-2">
      {items.map((r) => (
        <Card key={r.id}>
          <div className="p-5">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
              <FolderGit2 size={24} className="accent" />
              <div className="flex gap-2">
                <StatusBadge status={r.is_active ? "active" : "inactive"} />
                <Badge>
                  {r.is_private === null
                    ? "Visibility unknown"
                    : r.is_private
                      ? "Private"
                      : "Public"}
                </Badge>
              </div>
            </div>
            <Link
              href={`/repositories/${r.id}`}
              className="break-safe text-base font-semibold hover:underline"
              prefetch={false}
            >
              {r.full_name}
            </Link>
            <p className="muted mt-2 break-safe text-sm">
              {r.description ?? "No description provided."}
            </p>
            <div className="muted mt-4 flex flex-wrap gap-4 text-xs">
              <span>{r.primary_language ?? "Language not available"}</span>
              <span className="flex items-center gap-1 break-all">
                <GitBranch size={13} />
                {r.default_branch}
              </span>
            </div>
            <div className="mt-5 grid grid-cols-2 gap-3 border-t border-[var(--border)] pt-4">
              <div>
                <p className="text-2xl font-semibold">{r.pull_request_count}</p>
                <p className="muted text-xs">Pull requests</p>
              </div>
              <div>
                <p className="text-2xl font-semibold">
                  {r.open_pull_request_count}
                </p>
                <p className="muted text-xs">Open pull requests</p>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--border)] px-5 py-3">
            <p className="muted text-xs">
              Last sync {formatDate(r.last_synced_at, "Never")}
            </p>
            <GitHubLink url={r.html_url} />
          </div>
        </Card>
      ))}
    </div>
  );
}
