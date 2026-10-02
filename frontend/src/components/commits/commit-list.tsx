import { GitCommitHorizontal } from "lucide-react";
import type { Commit } from "@/types/commit";
import { Card, EmptyState } from "@/components/ui";
import { GitHubLink } from "@/components/ui/github-link";
import { formatDate } from "@/lib/utils";

export function CommitList({ items }: { items: Commit[] }) {
  if (!items.length) return <EmptyState title="No commits found." description="No synchronized commit metadata is available yet." />;
  return <div className="space-y-3">{items.map((commit) => <Card key={commit.id}><div className="flex flex-wrap items-start gap-4 p-5"><GitCommitHorizontal size={20} className="accent mt-1" /><div className="min-w-0 flex-1"><p className="break-safe font-semibold">{commit.title}</p><p className="muted mt-1 text-sm">{commit.repository_full_name} · {commit.author_login ?? commit.author_name ?? "Unknown author"}</p><p className="muted mt-2 font-mono text-xs">{commit.sha.slice(0, 12)} · {formatDate(commit.authored_at, "Unknown date")}</p></div><GitHubLink url={commit.html_url} /></div></Card>)}</div>;
}
