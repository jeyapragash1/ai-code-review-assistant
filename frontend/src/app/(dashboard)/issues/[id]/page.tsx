import { notFound } from "next/navigation";
import { CircleDot, MessageSquare } from "lucide-react";
import { getIssue } from "@/lib/api/issues";
import { load } from "@/lib/api/server";
import { isUuid } from "@/lib/api/parsers";
import { ApiState } from "@/components/ui/api-state";
import { Badge, Breadcrumbs, PageHeading, StatusBadge } from "@/components/ui";
import { GitHubLink } from "@/components/ui/github-link";
import { RefreshButton } from "@/components/ui/refresh-button";
import { formatDate } from "@/lib/utils";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!isUuid(id)) notFound();
  const result = await load(() => getIssue(id));
  if (!result.ok) { if (result.error === "not_found") notFound(); return <ApiState kind={result.error} />; }
  const issue = result.data;
  return <div className="page-stack"><Breadcrumbs items={[{ label: "Issues", href: "/issues" }, { label: `#${issue.github_issue_number}` }]} /><PageHeading title={`#${issue.github_issue_number} ${issue.title}`} description={issue.repository_full_name} action={<RefreshButton />} /><div className="flex flex-wrap items-center gap-3"><CircleDot size={20} className="accent" /><StatusBadge status={issue.state === "open" ? "active" : "inactive"} /><Badge>{issue.author_login ?? "Unknown author"}</Badge><GitHubLink url={issue.html_url} /></div><dl className="grid gap-4 border-y border-[var(--border)] py-5 sm:grid-cols-3"><div><dt className="muted text-xs">Updated</dt><dd className="mt-1 text-sm">{formatDate(issue.github_updated_at, "Unknown")}</dd></div><div><dt className="muted text-xs">Comments</dt><dd className="mt-1 flex items-center gap-1 text-sm"><MessageSquare size={14} />{issue.comment_count}</dd></div><div><dt className="muted text-xs">Labels</dt><dd className="mt-1 text-sm">{issue.labels.length}</dd></div></dl><section className="panel p-5"><h2 className="section-title">Issue body</h2><p className="muted mt-4 whitespace-pre-wrap text-sm leading-7">{issue.body ?? "No issue body provided."}</p></section></div>;
}
