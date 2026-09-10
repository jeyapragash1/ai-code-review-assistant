# Repository and Pull Request Read APIs

Start FastAPI from the backend directory:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another PowerShell window:

```powershell
$base = 'http://127.0.0.1:8000/api/v1'
Invoke-RestMethod "$base/dashboard/statistics"
$repositories = Invoke-RestMethod "$base/repositories?page=1&page_size=20&search=ai-code-review-assistant&is_active=true"
$repositories
if ($repositories.items.Count -gt 0) {
    $repositoryId = $repositories.items[0].id
    Invoke-RestMethod "$base/repositories/$repositoryId"
    Invoke-RestMethod "$base/repositories/$repositoryId/pull-requests?status=open&page_size=20"
    Invoke-RestMethod "$base/pull-requests?repository_id=$repositoryId&status=merged"
}
$pullRequests = Invoke-RestMethod "$base/pull-requests?page=1&page_size=20"
if ($pullRequests.items.Count -gt 0) {
    $pullRequestId = $pullRequests.items[0].id
    Invoke-RestMethod "$base/pull-requests/$pullRequestId"
}
```

No credentials are needed for these local read APIs. Keep the development server bound to loopback; authentication is not implemented yet. Synchronization is an administrative CLI command, not an HTTP route.

Pagination envelope: `items`, `total`, `page`, `page_size`, `total_pages`. Page sizes are 1-100, default 20; pages start at 1. Searches are literal case-insensitive substrings, at most 200 characters. UUIDs are internal database IDs, not GitHub IDs. PR status values are `open`, `closed`, and `merged`.

Repository items include GitHub identity/display metadata and total/open PR counts. PR items include repository identity, branches, author, status, draft flag, commit SHA, diff statistics, and timestamps. PR details additionally contain a `repository` summary. Dates are ISO 8601. New metadata on legacy rows may be null until synchronized.

Dashboard fields: `connected_repository_count`, `total_pull_request_count`, `open_pr_count`, `closed_pr_count`, `merged_pr_count`, `reviews_count`, `findings_count`, `high_severity_findings_count`, and `recently_updated_pull_requests`. Review and finding counts are zero until those features exist.

Errors use FastAPI's `detail` envelope: 404 for unknown records, 422 for invalid parameters, and a generic 503 for unavailable database data. Webhook payloads, database errors, credentials, and upstream response bodies are never returned. Existing `/health`, `/health/ready`, and signed webhook ingress retain their behavior.

Swagger: http://127.0.0.1:8000/docs. OpenAPI: http://127.0.0.1:8000/openapi.json.
