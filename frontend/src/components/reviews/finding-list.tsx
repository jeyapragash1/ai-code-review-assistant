import { FileCode2 } from "lucide-react";
import type { ReviewFinding } from "@/types/review";
import { formatConfidence, label } from "@/lib/utils";
import { Badge, EmptyState, StatusBadge } from "@/components/ui";

function lineLabel(finding: ReviewFinding) {
  if (finding.start_line === null) return "Line not available";
  if (finding.end_line !== null && finding.end_line !== finding.start_line)
    return `Lines ${finding.start_line}-${finding.end_line}`;
  return `Line ${finding.start_line}`;
}

function sourceLabel(source: ReviewFinding["source"]) {
  return source === "static"
    ? "Static analysis"
    : source === "ai"
      ? "AI analysis"
      : "Hybrid analysis";
}

export function FindingList({
  items,
  emptyTitle = "No findings found.",
  emptyDescription = "This review attempt has no persisted findings matching the current filters.",
}: {
  items: ReviewFinding[];
  emptyTitle?: string;
  emptyDescription?: string;
}) {
  if (!items.length)
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  return (
    <div className="space-y-4 p-4 sm:p-5">
      {items.map((finding) => (
        <article key={finding.id} className="bordered rounded-md p-4">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <Badge tone={finding.severity}>{label(finding.severity)}</Badge>
            <Badge>{label(finding.category)}</Badge>
            <Badge>{sourceLabel(finding.source)}</Badge>
            <StatusBadge status={finding.status} />
            <Badge>
              {finding.published_to_github
                ? "Published to GitHub"
                : "Not published to GitHub"}
            </Badge>
          </div>
          <h3 className="break-safe text-base font-semibold">
            {finding.title}
          </h3>
          <p className="muted mt-2 flex items-start gap-2 break-safe text-xs">
            <FileCode2 size={14} className="mt-0.5 shrink-0" />
            <span>
              {finding.file_path} · {lineLabel(finding)}
            </span>
          </p>
          <dl className="mt-4 grid gap-4 text-sm lg:grid-cols-2">
            <div>
              <dt className="muted text-xs">Problem</dt>
              <dd className="break-safe mt-1">{finding.problem}</dd>
            </div>
            {finding.explanation && (
              <div>
                <dt className="muted text-xs">Why it matters</dt>
                <dd className="break-safe mt-1">{finding.explanation}</dd>
              </div>
            )}
            {finding.suggestion && (
              <div>
                <dt className="muted text-xs">Suggested improvement</dt>
                <dd className="break-safe mt-1">{finding.suggestion}</dd>
              </div>
            )}
            <div>
              <dt className="muted text-xs">Confidence</dt>
              <dd className="mt-1">{formatConfidence(finding.confidence)}</dd>
            </div>
          </dl>
          {finding.code_snippet && (
            <pre className="code-preview mt-4">
              <code>{finding.code_snippet}</code>
            </pre>
          )}
        </article>
      ))}
    </div>
  );
}
