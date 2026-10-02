import test from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { spawn, execFile } from "node:child_process";
import { once } from "node:events";
import { setTimeout as delay } from "node:timers/promises";

// Opt in to the real Next dev-server rendering test. The API fixture is local,
// isolated and never calls GitHub or touches the application database.
test("authenticated pages render counts, empty/unavailable states and protected controls", { skip: process.env.RUN_PAGE_SMOKE !== "1", timeout: 180000 }, async () => {
  const id = "00000000-0000-4000-8000-000000000001", time = "2026-10-01T00:00:00Z";
  const page = items => ({ items, total: items.length, page: 1, page_size: 20, total_pages: items.length ? 1 : 0 });
  const user = { id, github_user_id: 1, github_login: "test-owner", display_name: null, email: null, avatar_url: null, profile_url: null, session_expires_at: time };
  const repository = { id, full_name: "test-owner/test-repo", html_url: "https://github.com/test-owner/test-repo", github_repository_id: 1,
    owner: "test-owner", name: "test-repo", description: null, default_branch: "main", primary_language: "Python", is_private: false,
    is_active: true, pull_request_count: 1, open_pull_request_count: 1, github_updated_at: time, last_synced_at: time, created_at: time, updated_at: time };
  const pr = { id, repository_id: id, repository_full_name: repository.full_name, github_pr_number: 2, title: "Synthetic page test PR", author_login: "test-owner",
    base_branch: "main", head_branch: "test", status: "open", is_draft: false, head_sha: "a".repeat(40), html_url: null,
    additions: 1, deletions: 0, changed_files: 1, github_created_at: time, github_updated_at: time, last_synced_at: time, created_at: time, updated_at: time,
    repository: { id, full_name: repository.full_name, html_url: repository.html_url } };
  const dashboard = { connected_repository_count: 1, total_pull_request_count: 1, open_pr_count: 1, closed_pr_count: 0, merged_pr_count: 0,
    total_reviews: 1, completed_reviews: 1, failed_reviews: 0, in_progress_reviews: 0, total_findings: 3, high_severity_findings: 1,
    reviews_count: 1, findings_count: 3, high_severity_findings_count: 1, recently_updated_pull_requests: [] };
  const keys = ["repositories_total", "repositories_public", "repositories_private", "repositories_fork", "repositories_archived", "repositories_inactive", "pull_requests_total", "pull_requests_open", "pull_requests_closed", "pull_requests_merged", "pull_requests_draft", "issues_total", "issues_open", "issues_closed", "recent_commits", "captured_push_events", "recent_activity", "review_jobs_queued", "review_jobs_processing", "review_jobs_completed", "review_jobs_failed", "review_jobs_retryable", "reviews_completed", "findings_total", "findings_high"];
  const account = { since: time, until: time, counts: { ...Object.fromEntries(keys.map(k => [k, 0])), repositories_total: 1, repositories_public: 1,
    pull_requests_total: 1, pull_requests_open: 1, recent_commits: 12, reviews_completed: 1, findings_total: 3, findings_high: 1 },
    findings_by_severity: { high: 1, low: 2 }, findings_by_category: { security: 1, validation: 2 }, findings_by_repository: { [id]: 3 },
    recent_commits: [], recent_activity: [], recently_updated_repositories: [], most_active_repositories: [], activity_metric: "Commits plus captured webhook events in the period." };
  let activityUnavailable = false, jobStatus = "queued";
  const requests = [];
  const api = createServer((request, response) => {
    const url = new URL(request.url, "http://localhost");
    requests.push(url);
    response.setHeader("content-type", "application/json");
    if (!request.headers.cookie?.includes("codereview_session=synthetic_page_session")) { response.writeHead(401); response.end("{}"); return; }
    let body;
    if (url.pathname === "/api/v1/auth/me") body = user;
    else if (url.pathname === "/api/v1/dashboard/statistics") body = dashboard;
    else if (url.pathname === "/api/v1/dashboard/account-statistics") body = account;
    else if (url.pathname === "/api/v1/github/sync/status") body = { app_configured: true, private_key_configured: true, webhook_configured: true, installation_count: 1, accessible_repository_count: 1, last_synchronized_at: time, last_result: "completed", safe_error: null };
    else if (url.pathname === "/api/v1/github/installations") body = [{ id: 1, account_login: "test-owner", is_active: true, repository_count: 1, last_synced_at: time }];
    else if (url.pathname === "/api/v1/github/sync" && request.method === "POST") { response.statusCode = 202; body = { status: "completed" }; }
    else if (url.pathname === "/api/v1/activity") { if (activityUnavailable) response.statusCode = 503; body = activityUnavailable ? { detail: "private fixture error" } : page([]); }
    else if (url.pathname === `/api/v1/repositories/${id}`) body = repository;
    else if (url.pathname === `/api/v1/repositories/${id}/pull-requests`) body = page([pr]);
    else if (url.pathname === `/api/v1/pull-requests/${id}`) body = pr;
    else if (url.pathname === "/api/v1/pull-requests") body = page([pr]);
    else if (url.pathname === `/api/v1/pull-requests/${id}/reviews`) body = page([]);
    else if (url.pathname === `/api/v1/pull-requests/${id}/review-jobs`) body = { id, head_sha: pr.head_sha, status: jobStatus, retry_count: 1, review_id: null, error_message: jobStatus === "failed" ? "Safe review failure" : null };
    else { response.statusCode = 404; body = {}; }
    response.end(JSON.stringify(body));
  });
  api.listen(0, "127.0.0.1");
  await once(api, "listening");
  const portProbe = createServer();
  portProbe.listen(0, "127.0.0.1");
  await once(portProbe, "listening");
  const frontendPort = portProbe.address().port;
  await new Promise(resolve => portProbe.close(resolve));
  const child = spawn(process.execPath, ["node_modules/next/dist/bin/next", "dev", "--hostname", "127.0.0.1", "--port", String(frontendPort)], {
    cwd: process.cwd(), windowsHide: true, stdio: ["ignore", "pipe", "pipe"], env: { ...process.env, NEXT_TELEMETRY_DISABLED: "1", NEXT_PUBLIC_API_BASE_URL: `http://127.0.0.1:${api.address().port}/api/v1` },
  });
  child.stdout.resume(); child.stderr.resume();
  const origin = `http://127.0.0.1:${frontendPort}`;
  const headers = { Cookie: "codereview_session=synthetic_page_session" };
  try {
    let ready = false;
    for (let i = 0; i < 120; i++) {
      try { await fetch(origin + "/login"); ready = true; break; } catch { await delay(500); }
    }
    assert.ok(ready, "Owned Next server started");
    const anonymous = await fetch(origin + "/activity", { redirect: "manual" });
    if (anonymous.status === 307) assert.match(anonymous.headers.get("location"), /\/login/);
    else {
      // Next can deliver a redirect in the streamed response after sending 200.
      assert.equal(anonymous.status, 200);
      assert.match(await anonymous.text(), /NEXT_REDIRECT|http-equiv="refresh"[^>]*login/);
    }
    let html = await (await fetch(origin + "/activity?event_type=push&actor=test-owner", { headers })).text();
    assert.match(html, /No captured activity/);
    assert.match(html, /Permanent activity begins/);
    assert.ok(requests.some(url => url.pathname === "/api/v1/activity" && url.searchParams.get("event_type") === "push"));
    html = await (await fetch(origin + "/activity?page=invalid", { headers })).text();
    assert.match(html, /Check your filters/);
    activityUnavailable = true;
    html = await (await fetch(origin + "/activity", { headers })).text();
    assert.match(html, /API unavailable/);
    assert.doesNotMatch(html, /private fixture error/);
    html = await (await fetch(origin + "/dashboard", { headers })).text();
    assert.match(html, /recent commits/); assert.match(html, />12</);
    html = await (await fetch(origin + "/settings", { headers })).text();
    assert.match(html, /Sync GitHub/); assert.match(html, /test-owner/); assert.match(html, /Ready/);
    const forbidden = await fetch(origin + "/api/github/sync", { method: "POST", headers });
    assert.equal(forbidden.status, 403);
    const accepted = await fetch(origin + "/api/github/sync", { method: "POST", headers: { ...headers, Origin: origin } });
    assert.equal(accepted.status, 202); assert.deepEqual(await accepted.json(), { status: "accepted" });
    for (jobStatus of ["queued", "processing", "completed", "failed"]) {
      html = await (await fetch(origin + `/pull-requests/${id}`, { headers })).text();
      assert.match(html, new RegExp(`${jobStatus}.*Attempt`));
      assert.match(html, /Run review/);
      if (jobStatus === "failed") assert.match(html, /Safe review failure/);
    }
    html = await (await fetch(origin + `/repositories/${id}`, { headers })).text();
    assert.match(html, /Repository sections/); assert.match(html, /Access state/); assert.match(html, /issues\?repository_id/); assert.match(html, /activity\?repository_id/);
  } finally {
    // Only this test's subprocess and its descendants are terminated.
    if (process.platform === "win32" && child.pid) await new Promise(resolve => execFile("taskkill", ["/PID", String(child.pid), "/T", "/F"], { windowsHide: true }, resolve));
    else child.kill("SIGTERM");
    await new Promise(resolve => api.close(resolve));
  }
});
