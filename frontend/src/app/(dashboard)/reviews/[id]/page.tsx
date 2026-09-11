import { notFound } from "next/navigation";
import { GitCommitHorizontal, ShieldAlert, ShieldCheck } from "lucide-react";
import type { SearchParams } from "@/types/api";
import {
  filePathQuery,
  findingCategoryQuery,
  findingSeverityQuery,
  findingSourceQuery,
  findingStatusQuery,
  paginationQuery,
} from "@/lib/api/filters";
import { isUuid } from "@/lib/api/parsers";
import { getReview, getReviewFindings } from "@/lib/api/reviews";
import { load } from "@/lib/api/server";
import {
  FINDING_CATEGORIES,
  FINDING_SEVERITIES,
  FINDING_SOURCES,
  FINDING_STATUSES,
} from "@/types/review";
import {
  Badge,
  Breadcrumbs,
  Button,
  Card,
  Input,
  PageHeading,
  Select,
  StatCard,
  StatusBadge,
} from "@/components/ui";
import { ApiState } from "@/components/ui/api-state";
import { FindingList } from "@/components/reviews/finding-list";
import { Pagination } from "@/components/ui/pagination";
import { RefreshButton } from "@/components/ui/refresh-button";
import {
  formatDateTime,
  formatDuration,
  label,
  shortSha,
} from "@/lib/utils";

const inProgress = new Set([
  "queued",
  "fetching",
  "static_analysis",
  "ai_analysis",
  "validating",
  "publishing",
]);

export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<SearchParams>;
}) {
  const { id } = await params;
  if (!isUuid(id)) notFound();
  const filters = await searchParams;
  const result = await load(async () => {
    const query = {
      ...paginationQuery(filters),
      severity: findingSeverityQuery(filters),
      category: findingCategoryQuery(filters),
      status: findingStatusQuery(filters),
      source: findingSourceQuery(filters),
      file_path: filePathQuery(filters),
    };
    const review = await getReview(id);
    const summary = await getReviewFindings(id, { page_size: 100 });
    const findings = await getReviewFindings(id, query);
    return { review, summary, findings, query };
  });
  if (!result.ok) {
    if (result.error === "not_found") notFound();
    return <ApiState kind={result.error} />;
  }
  const { review, summary, findings, query } = result.data;
  const severityCounts = FINDING_SEVERITIES.map((severity) => ({
    severity,
    count: summary.items.filter((finding) => finding.severity === severity)
      .length,
  }));
  const categoryCounts = FINDING_CATEGORIES.map((category) => ({
    category,
    count: summary.items.filter((finding) => finding.category === category)
      .length,
  })).filter((item) => item.count > 0);
  const terminalFailed = review.status === "failed";
  const running = inProgress.has(review.status);
  const path = `/reviews/${review.id}`;
  return (
    <div className="page-stack">
      <Breadcrumbs
        items={[
          { label: "Reviews", href: "/reviews" },
          {
            label: review.pull_request.repository_full_name,
            href: `/repositories/${review.pull_request.repository_id}`,
          },
          {
            label: `PR #${review.pull_request.github_pr_number}`,
            href: `/pull-requests/${review.pull_request_id}`,
          },
          { label: `Attempt ${review.attempt_number}` },
        ]}
      />
      <PageHeading
        title={`Review attempt ${review.attempt_number}`}
        description={`${review.pull_request.title} · ${review.pull_request.repository_full_name}`}
        action={<RefreshButton />}
      />
      <div className="flex flex-wrap items-center gap-3">
        <StatusBadge status={review.status} />
        {review.overall_risk && (
          <Badge tone={review.overall_risk}>
            Risk: {label(review.overall_risk)}
          </Badge>
        )}
        <Badge>{label(review.trigger_type)} trigger</Badge>
        <span
          title={review.commit_sha}
          aria-label={`Commit ${review.commit_sha}`}
          className="flex items-center gap-1 font-mono text-xs"
        >
          <GitCommitHorizontal size={14} />
          {shortSha(review.commit_sha)}
        </span>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Findings"
          value={review.findings_count}
          detail="Persisted for this attempt"
          icon={<ShieldCheck size={17} />}
        />
        <StatCard
          label="High severity"
          value={review.high_severity_findings_count}
          detail="Requires priority review"
          icon={<ShieldAlert size={17} />}
          tone="text-[var(--red)]"
        />
        <StatCard
          label="Started"
          value={formatDateTime(review.started_at)}
          detail="UTC"
          icon={<ShieldCheck size={17} />}
        />
        <StatCard
          label="Duration"
          value={formatDuration(review.duration_ms)}
          detail="Backend recorded time"
          icon={<ShieldCheck size={17} />}
        />
      </div>
      {terminalFailed && (
        <Card className="p-5">
          <h2 className="mb-2 font-semibold">Failed attempt</h2>
          <p className="muted text-sm">
            This attempt did not complete, so no completed findings are
            available for it.
          </p>
          <dl className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <dt className="muted text-xs">Safe error code</dt>
              <dd className="break-safe mt-1">
                {review.error_code ?? "Not available"}
              </dd>
            </div>
            <div>
              <dt className="muted text-xs">Safe message</dt>
              <dd className="break-safe mt-1">
                {review.error_message ?? "No safe error message was recorded."}
              </dd>
            </div>
          </dl>
        </Card>
      )}
      {running && (
        <Card className="p-5">
          <h2 className="mb-2 font-semibold">Review still running</h2>
          <p className="muted text-sm">
            Results will appear after the backend marks this attempt as
            completed. Static analysis is available; Gemini analysis is not
            enabled yet.
          </p>
        </Card>
      )}
      {review.status === "completed" && (
        <>
          <Card className="p-5">
            <div className="panel-head -m-5 mb-5">
              <h2>Finding summary</h2>
            </div>
            {summary.total === 0 ? (
              <p className="muted text-sm">
                This completed review has zero persisted findings.
              </p>
            ) : (
              <div className="grid gap-5 lg:grid-cols-2">
                <dl className="space-y-3">
                  {severityCounts.map((item) => (
                    <div
                      key={item.severity}
                      className="flex items-center justify-between gap-3"
                    >
                      <dt>
                        <Badge tone={item.severity}>
                          {label(item.severity)}
                        </Badge>
                      </dt>
                      <dd className="font-semibold tabular-nums">
                        {item.count}
                      </dd>
                    </div>
                  ))}
                </dl>
                <dl className="space-y-3">
                  {categoryCounts.map((item) => (
                    <div
                      key={item.category}
                      className="flex items-center justify-between gap-3"
                    >
                      <dt>{label(item.category)}</dt>
                      <dd className="font-semibold tabular-nums">
                        {item.count}
                      </dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}
          </Card>
          <Card>
            <div className="panel-head">
              <h2>Findings</h2>
            </div>
            <form
              method="get"
              action={path}
              className="flex flex-wrap items-end gap-3 border-b border-[var(--border)] p-5"
            >
              <input type="hidden" name="page" value="1" />
              <Select
                label="Severity"
                name="severity"
                defaultValue={String(query.severity ?? "")}
              >
                <option value="">All severities</option>
                {FINDING_SEVERITIES.map((severity) => (
                  <option key={severity} value={severity}>
                    {label(severity)}
                  </option>
                ))}
              </Select>
              <Select
                label="Category"
                name="category"
                defaultValue={String(query.category ?? "")}
              >
                <option value="">All categories</option>
                {FINDING_CATEGORIES.map((category) => (
                  <option key={category} value={category}>
                    {label(category)}
                  </option>
                ))}
              </Select>
              <Select
                label="Status"
                name="status"
                defaultValue={String(query.status ?? "")}
              >
                <option value="">All statuses</option>
                {FINDING_STATUSES.map((status) => (
                  <option key={status} value={status}>
                    {label(status)}
                  </option>
                ))}
              </Select>
              <Select
                label="Source"
                name="source"
                defaultValue={String(query.source ?? "")}
              >
                <option value="">All sources</option>
                {FINDING_SOURCES.map((source) => (
                  <option key={source} value={source}>
                    {label(source)}
                  </option>
                ))}
              </Select>
              <div className="min-w-0 flex-[1_1_220px]">
                <Input
                  label="File path"
                  name="file_path"
                  maxLength={1024}
                  defaultValue={String(query.file_path ?? "")}
                  placeholder="evaluation/fixtures"
                />
              </div>
              <div className="w-24">
                <Input
                  label="Page size"
                  name="page_size"
                  type="number"
                  min={1}
                  max={100}
                  required
                  defaultValue={String(query.page_size ?? 20)}
                />
              </div>
              <Button type="submit" className="primary">
                Apply
              </Button>
              <a className="button" href={path}>
                Clear
              </a>
            </form>
            <FindingList
              items={findings.items}
              emptyTitle={
                summary.total === 0
                  ? "No findings for this completed review."
                  : "No findings match these filters."
              }
            />
          </Card>
          <Pagination path={path} data={findings} query={query} />
        </>
      )}
    </div>
  );
}
