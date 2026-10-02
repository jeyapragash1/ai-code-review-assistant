import test from "node:test";
import assert from "node:assert/strict";
import { parseActivity, parseAccountStatistics, parseInstallations, parseSyncStatus, parseReviewJob, parsePage } from "../src/lib/api/parsers.ts";
import { getActivity } from "../src/lib/api/activity.ts";

const id = "00000000-0000-4000-8000-000000000001";
const time = "2026-10-01T00:00:00Z";
test("activity validates dates, UUIDs and empty pages without source payloads", () => {
  const event = { id, repository_id: id, installation_id: id, actor_login: "owner", event_type: "push", event_action: null,
    event_at: time, received_at: time, processing_status: "completed", retry_count: 1, error_message: null, payload: { secret: "excluded" } };
  assert.equal(parseActivity(event).event_type, "push");
  assert.equal("payload" in parseActivity(event), false);
  assert.throws(() => parseActivity({ ...event, event_at: "yesterday" }));
  assert.throws(() => parseActivity({ ...event, id: "mock-1" }));
  assert.equal(parsePage({ items: [], total: 0, page: 1, page_size: 20, total_pages: 0 }, parseActivity).total, 0);
});
test("account dashboard preserves nonzero counts and rejects missing or negative aggregates", () => {
  const keys = ["repositories_total", "repositories_public", "repositories_private", "repositories_fork", "repositories_archived", "repositories_inactive", "pull_requests_total", "pull_requests_open", "pull_requests_closed", "pull_requests_merged", "pull_requests_draft", "issues_total", "issues_open", "issues_closed", "recent_commits", "captured_push_events", "recent_activity", "review_jobs_queued", "review_jobs_processing", "review_jobs_completed", "review_jobs_failed", "review_jobs_retryable", "reviews_completed", "findings_total", "findings_high"];
  const body = { since: time, until: time, counts: Object.fromEntries(keys.map(k => [k, 7])), findings_by_severity: { high: 3 }, findings_by_category: { security: 3 }, findings_by_repository: { [id]: 3 },
    recent_commits: [], recent_activity: [], recently_updated_repositories: [], most_active_repositories: [], activity_metric: "Commits plus events" };
  assert.equal(parseAccountStatistics(body).counts.repositories_private, 7);
  assert.equal(parseAccountStatistics(body).findings_by_category.security, 3);
  assert.throws(() => parseAccountStatistics({ ...body, counts: {} }));
  assert.throws(() => parseAccountStatistics({ ...body, counts: { ...body.counts, issues_open: -1 } }));
});
test("Settings validates readiness and review jobs validate every state", () => {
  const s = parseSyncStatus({ app_configured: true, private_key_configured: true, webhook_configured: true, installation_count: 1, accessible_repository_count: 3, last_synchronized_at: time, last_result: "completed", safe_error: null });
  assert.equal(s.accessible_repository_count, 3);
  assert.throws(() => parseInstallations([{ id: 1, account_login: "owner", is_active: "yes", repository_count: 3, last_synced_at: time }]));
  for (const status of ["queued", "processing", "completed", "failed", "retryable"]) assert.equal(parseReviewJob({ id, head_sha: "a".repeat(40), status, retry_count: 1, review_id: null, error_message: null }).status, status);
  assert.equal(parseReviewJob(null), null);
  assert.throws(() => parseReviewJob({ id, status: "fake" }));
});
test("activity unavailable and malformed responses never return sample activity", async () => {
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async () => { throw new Error("offline"); };
    await assert.rejects(getActivity(), error => error.kind === "unavailable");
    globalThis.fetch = async () => new Response(JSON.stringify({ items: ["fake"], total: 1, page: 1, page_size: 20, total_pages: 1 }), { status: 200 });
    await assert.rejects(getActivity(), error => error.kind === "unexpected");
  } finally { globalThis.fetch = original; }
});
