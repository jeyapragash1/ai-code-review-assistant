import Link from "next/link";
import { CircleDot, MessageSquare } from "lucide-react";
import type { Issue } from "@/types/issue";
import { Badge, Card, EmptyState, StatusBadge } from "@/components/ui";
import { GitHubLink } from "@/components/ui/github-link";
import { formatDate } from "@/lib/utils";

export function IssueList({ items }: { items: Issue[] }) {
  if (!items.length) return <EmptyState title="No issues found." description="No synchronized GitHub issues match these filters. Pull Requests are not counted as issues." />;
  return <div className="grid gap-5 lg:grid-cols-2">{items.map((issue) => <Card key={issue.id}><div className="p-5"><div className="mb-4 flex items-center justify-between gap-3"><CircleDot size={22} className="accent" /><StatusBadge status={issue.state === "open" ? "active" : "inactive"} /></div><Link href={`/issues/${issue.id}`} prefetch={false} className="break-safe text-base font-semibold hover:underline">#{issue.github_issue_number} {issue.title}</Link><p className="muted mt-2 text-sm">{issue.repository_full_name} · {issue.author_login ?? "Unknown author"}</p><div className="muted mt-4 flex flex-wrap gap-4 text-xs"><span className="flex items-center gap-1"><MessageSquare size={13} />{issue.comment_count} comments</span><span>Updated {formatDate(issue.github_updated_at, "Unknown")}</span></div></div><div className="flex items-center justify-between border-t border-[var(--border)] px-5 py-3"><Badge>{issue.labels.length} labels</Badge><GitHubLink url={issue.html_url} /></div></Card>)}</div>;
}
