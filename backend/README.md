# AI-Powered GitHub Code Review Assistant API

FastAPI backend foundation for automated GitHub pull request analysis and code review.

## Requirements

- Python 3.12
- PostgreSQL running locally
- Database: `ai_code_review_db`
- Login role: `ai_code_review_app`

## Setup

From the `backend` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Configuration

Create `backend/.env` from `.env.example` and set local values:

```powershell
Copy-Item .env.example .env
```

`DATABASE_URL` should point to the local PostgreSQL database using the `ai_code_review_app` role. Keep `.env` private and never commit real credentials.

## Run

```powershell
python -m uvicorn app.main:app --reload
```

Windows development note:

On Windows, keep `--reload` for local development with the installed Uvicorn/Psycopg versions. Plain `python -m uvicorn` can create a Proactor event loop before importing the app, which Psycopg async does not support. For a server without reload, configure the Selector policy before Uvicorn starts:

```powershell
python -c "from app.core.asyncio import configure_asyncio_event_loop_policy; configure_asyncio_event_loop_policy(); import uvicorn; uvicorn.run('app.main:app', host='127.0.0.1', port=8000)"
```

Documentation URLs:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`
- `http://127.0.0.1:8000/openapi.json`

## Test

```powershell
python -m pytest
```

## Database

The backend uses SQLAlchemy 2 async sessions with Psycopg 3. FastAPI disposes database connections during application shutdown.

The GitHub ingestion and review-foundation tables are:

- `repositories`: stores synchronized GitHub repository identity and display metadata. It does not store GitHub tokens or secrets.
- `pull_requests`: stores pull request identity and review-target metadata for a repository. Pull requests are deleted when their stored repository is deleted.
- `webhook_events`: stores unique GitHub webhook deliveries for later asynchronous processing and retry support.
- `reviews`: stores one review run for a Pull Request commit/attempt, including safe status, trigger, model metadata, timing, token usage, estimated cost, and safe error information. Reviews are deleted when their stored Pull Request is deleted.
- `review_findings`: stores individual findings for a review, including file/line location, severity, category, source, confidence, deterministic fingerprint, optional safe snippet, and GitHub publication metadata. Findings are deleted when their stored review is deleted.

Webhook payloads may contain sensitive metadata. Do not log, print, or expose raw webhook payload contents.
Review prompts, provider secrets, raw API keys, webhook payloads, and database URLs are not stored in the review tables and must not be exposed through logs or API responses.

Alembic is configured for async SQLAlchemy and reads `DATABASE_URL` from the application settings:

```powershell
python -m alembic current
python -m alembic upgrade head
python -m alembic revision --autogenerate -m "describe change"
```

Inspect the active Alembic revision with:

```powershell
python -m alembic current
```

## Health Checks

- `GET /api/v1/health` is a lightweight liveness check and does not require PostgreSQL.
- `GET /api/v1/health/ready` checks PostgreSQL with a safe `SELECT 1` and returns `503` if the database is unavailable.

## GitHub Webhook Ingress

`POST /api/v1/webhooks/github` receives GitHub webhook deliveries. A real GitHub webhook will be configured in a later task.

Required headers:

- `X-Hub-Signature-256`
- `X-GitHub-Event`
- `X-GitHub-Delivery`

Supported events for this phase:

- `ping`
- `pull_request` with actions `opened`, `synchronize`, `reopened`, and `closed`

Response behavior:

- `200`: authenticated `ping` returns `pong`, or a duplicate delivery returns `duplicate`.
- `202`: supported pull request deliveries return `accepted`; unsupported events/actions return `ignored`.
- `400`: malformed headers, invalid JSON, or a non-object JSON payload.
- `401`: missing or invalid webhook signature.
- `413`: declared or actual body size exceeds `GITHUB_WEBHOOK_MAX_BODY_BYTES`.
- `415`: content type is not `application/json`.
- `503`: server misconfiguration or persistence failure.

Signature verification uses HMAC-SHA256 with `GITHUB_WEBHOOK_SECRET` over the exact raw request bytes and compares the `sha256=` signature with constant-time comparison. The raw body is never parsed before signature verification.

`GITHUB_WEBHOOK_MAX_BODY_BYTES` defaults to `2097152` bytes. Both `Content-Length`, when provided, and the actual bytes read are checked.

`X-GitHub-Delivery` is the idempotency key. Duplicate delivery IDs never create a second `webhook_events` row.

For safe local testing, use a disposable secret in `.env`, calculate `X-Hub-Signature-256` over the exact request body bytes, and send only synthetic JSON payloads. Never expose the webhook secret, signature, raw request body, decoded payload, tokens, or repository source code in logs, screenshots, terminal output, or commits.

## Repository and Pull Request Synchronization

The administrative CLI uses GitHub REST API -> typed Pydantic normalization -> repository stores -> one PostgreSQL transaction. HTTP access lives in `app/clients/github.py`, orchestration in `app/services/github/repository_sync.py`, persistence in `app/repositories/`, and explicit API response contracts in `app/schemas/`. Webhook receipt remains independent of synchronization.

Public repositories work without a token. Empty values and placeholders such as `replace-with-github-token` are treated as missing; no Authorization header is sent. An optional genuine `GITHUB_TOKEN` is used as a bearer token, and GitHub decides whether it is valid. Authentication failures are not retried or silently downgraded to anonymous access. Never print tokens or headers.

Safe defaults (already used when absent from your existing private `.env`):

```env
GITHUB_API_BASE_URL=https://api.github.com
GITHUB_API_VERSION=2026-03-10
GITHUB_REPOSITORY_OWNER=Jeyapragash1
GITHUB_REPOSITORY_NAME=ai-code-review-assistant
GITHUB_REQUEST_TIMEOUT_SECONDS=15
GITHUB_MAX_RETRIES=3
```

The base URL is restricted to GitHub's official API. Version `2026-03-10` is the newest supported version checked against [GitHub's official version documentation](https://docs.github.com/en/rest/about-the-rest-api/api-versions). Requests send `application/vnd.github+json`, the version header, and a descriptive User-Agent. Owner and repository path segments are validated, redirects are not followed, and pagination links must remain on the same trusted endpoint with an advancing page number. Only the validated page number is reused; arbitrary link URLs are never requested.

The client follows all pages with `state=all`, `sort=updated`, and `direction=desc`, deduplicates PR numbers, and retrieves each PR's details for accurate additions, deletions, changed files, and merged status. Detail requests are sequential (concurrency one). Connection and response timeouts are bounded. Network failures and selected 429/5xx responses have bounded retries; authentication, permission, validation, and not-found responses do not. Short Retry-After delays are respected. A delay exceeding five seconds aborts safely for a later manual run instead of sleeping indefinitely or retrying early.

Run from `backend/` after activating the Python 3.12 virtual environment:

```powershell
python -m alembic upgrade head
python -m alembic current
python -m alembic check
python -m app.cli.sync_repository
# Optional validated administrative overrides:
python -m app.cli.sync_repository --owner Jeyapragash1 --repo ai-code-review-assistant
```

The CLI prints only a typed summary (repository created/updated; PRs created/updated/unchanged; total processed; UTC synchronization time). Failures return exit code 1 with a safe message. HTTP and database resources are closed. It never prints upstream bodies, tokens, connection strings, or SQL exceptions. Synchronization is CLI-only; there is no public POST sync route.

All remote reads finish before a database transaction starts. A transaction-scoped advisory lock serializes sync writers for one GitHub repository ID. PostgreSQL unique constraints and conflict-aware inserts preserve UUIDs and prevent duplicate repositories/PRs. Newer stored GitHub timestamps are not overwritten by older snapshots. Repository installation IDs and local active preferences are preserved. `last_synced_at` advances even for unchanged PRs; this timestamp alone does not count as a content update. Any persistence failure rolls back the entire write transaction. No synchronization path deletes existing rows.

Repository metadata now includes HTML URL, description, primary language, privacy, GitHub update time, and sync time. PR metadata includes draft state, diff statistics, and sync time. New metadata columns are nullable for preexisting unsynchronized rows; null means unknown, not zero. Successfully synchronized records populate these values from GitHub. Database checks reject negative diff statistics. Existing migrations and webhook tables are preserved.

Migration `2b28dd1f97e6` adds this metadata on top of ingestion revision `3e822f7f035f`. Its downgrade removes only the new metadata fields, indexes, and checks; it leaves ingestion tables and their original constraints intact.

GitHub pagination is not a snapshot: PR updates during a long run can shift page boundaries. Duplicate numbers are deduplicated; no absent record is deleted, and another CLI run refreshes the data. No background worker or periodic synchronization is configured.

## Read-only Data APIs

- `GET /api/v1/dashboard/statistics`
- `GET /api/v1/repositories`
- `GET /api/v1/repositories/{repository_id}`
- `GET /api/v1/repositories/{repository_id}/pull-requests`
- `GET /api/v1/pull-requests`
- `GET /api/v1/pull-requests/{pull_request_id}`
- `GET /api/v1/pull-requests/{pull_request_id}/reviews`
- `GET /api/v1/reviews`
- `GET /api/v1/reviews/{review_id}`
- `GET /api/v1/reviews/{review_id}/findings`
- `GET /api/v1/review-findings/{finding_id}`

Details use internal UUIDs. Lists return `items`, `total`, `page`, `page_size`, and `total_pages`; empty lists have zero total pages. `page` starts at 1 (maximum 1,000,000), and `page_size` defaults to 20 with a maximum of 100. Invalid parameters return 422, unknown detail records return 404, and database failures return generic 503 responses.

Repository filters: `search` (literal case-insensitive substring of full name) and `is_active`. PR filters: `search` (title or author), `repository_id`, and `status=open|closed|merged`. Nested repository PRs support pagination and status. Search is limited to 200 characters and escapes SQL LIKE wildcards. Repository lists order by last sync/local update; PRs order by GitHub update time, nulls last. Both use UUID tie-breakers. Grouped SQL counts and joined repository summaries avoid N+1 queries.

Review filters: `pull_request_id`, `repository_id`, `status`, `overall_risk`, and `commit_sha`. Finding filters: `severity`, `category`, `status`, `source`, and `file_path`. Review statuses are `queued`, `fetching`, `static_analysis`, `ai_analysis`, `validating`, `publishing`, `completed`, and `failed`. Risk values are `none`, `low`, `medium`, and `high`. Finding severity values are `high`, `medium`, and `low`.

Dashboard statistics count active repositories, real PR states, real review rows, real finding rows, and real high-severity findings. No mock data, fabricated risk scores, or review activity is returned. Until the review engine exists, review/finding counts remain zero unless rows are created by a future internal orchestration path.

The review tables are read-only over HTTP in this phase. Internal repository helpers can create review runs, mark review status, and insert findings idempotently by fingerprint for future orchestration, but there are no public create/update/delete review routes.

See [API examples](../docs/api/read-api.md). Automated tests use HTTPX MockTransport and dependency/session doubles; they never call GitHub or insert production test data.

## Static Review Pipeline

The first real review runner is an administrative CLI-only static-analysis pipeline. It loads a synchronized Pull Request from PostgreSQL, uses its stored head SHA, fetches changed-file metadata through GitHub's Pull Request files API, downloads exact file contents from GitHub's Contents API at that head SHA, analyzes supported Python files, normalizes findings, and persists one real `reviews` row with associated `review_findings`.

Run from `backend/`:

```powershell
python -m app.cli.review_pull_request --repository jeyapragash1/ai-code-review-assistant --pr-number 1
# Or by internal database UUID:
python -m app.cli.review_pull_request --pull-request-id <pull-request-uuid>
# Force a new attempt for the same commit:
python -m app.cli.review_pull_request --repository jeyapragash1/ai-code-review-assistant --pr-number 1 --force
```

Normal runs are idempotent for a Pull Request and commit SHA: if a completed review already exists, the CLI returns that review summary and does not create duplicate findings. `--force` creates the next attempt number. Attempt numbers are calculated while locking the stored Pull Request row, and the database uniqueness constraint on `(pull_request_id, commit_sha, attempt_number)` remains the final concurrency guard.

Supported file type for this milestone: Python (`.py`). Deleted files, unsafe paths, unsupported extensions, binary content, unsupported encodings, oversized files, excessive total bytes, excessive patch metadata, and files beyond the changed-file limit are skipped with safe reason codes. Repository paths are normalized and rejected if they are absolute, Windows drive paths, contain null bytes, backslashes, or `..` traversal. Fetched files are written only to an application-created temporary directory, which is removed after analysis.

Current static analyzers:

- Bandit: JSON output for Python security findings such as SQL query construction risks. Application code invokes Bandit with controlled arguments against the temporary directory.
- Ruff: JSON output with repository configuration disabled via `--isolated`; this milestone selects `BLE001` to catch broad exception handling without noisy formatting rules.
- Conservative AST validation analyzer: local, explainable parameter-flow checks for obvious unvalidated function parameters reaching SQL-sensitive construction or execution. It recognizes simple local validation evidence such as type checks, comparisons, assertions, conversions, and guard clauses that raise or return. It is not full interprocedural taint analysis, so false positives and false negatives are expected.

Analyzer subprocesses use argument arrays, `shell=False`, captured output, controlled working directories, minimal environment variables, and bounded timeouts. Exit codes that mean "findings detected" are treated as successful analysis. Tool crashes, timeouts, malformed JSON, GitHub fetch failures, and persistence failures are converted into safe failed-review states without tracebacks or raw tool output in API responses.

Normalized findings use deterministic SHA-256 fingerprints derived from stable fields such as analyzer, rule, path, line, category, severity, and title. Volatile data, UUIDs, timestamps, absolute temporary paths, raw source, provider payloads, and secrets are not included. Findings are deduplicated, sorted deterministically, capped by `STATIC_REVIEW_MAX_FINDINGS`, and stored without snippets for now to avoid persisting accidental credentials.

Static review settings:

```env
STATIC_REVIEW_MAX_CHANGED_FILES=50
STATIC_REVIEW_MAX_FILE_BYTES=262144
STATIC_REVIEW_MAX_TOTAL_BYTES=1048576
STATIC_REVIEW_ANALYZER_TIMEOUT_SECONDS=10
STATIC_REVIEW_MAX_FINDINGS=100
STATIC_REVIEW_MAX_PATCH_BYTES=131072
STATIC_REVIEW_MAX_TITLE_LENGTH=255
STATIC_REVIEW_MAX_PROBLEM_LENGTH=2000
STATIC_REVIEW_MAX_EXPLANATION_LENGTH=2000
STATIC_REVIEW_MAX_SUGGESTION_LENGTH=2000
STATIC_REVIEW_VALIDATION_CONFIDENCE_THRESHOLD=0.8
```

The CLI prints only a concise safe JSON summary: review UUID, Pull Request number, commit SHA, status, risk, finding counts, skipped-file reason counts, and elapsed time. It never prints tokens, database URLs, request headers, raw GitHub responses, downloaded source, analyzer raw output, webhook payloads, or environment values.

Gemini, GitHub comments, webhook-triggered execution, background queues, and authenticated public review-trigger endpoints remain deferred. This protects the public application surface until authentication, job controls, and publishing policy are designed.
