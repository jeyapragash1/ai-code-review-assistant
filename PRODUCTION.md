# Production operations

## GitHub App setup (manual)

Repository permissions: **Metadata: read**, **Contents: read**, **Pull requests: read**, **Issues: read**. The `repository` event uses Metadata read permission. This application does not publish reviews or comments; write permissions are unnecessary for its current workers. Confirm permission requirements against [GitHub's endpoint permission matrix](https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps) before changing App permissions.

Enable `push`, `pull_request`, `issues`, `issue_comment`, `pull_request_review`, `pull_request_review_comment`, and `repository`. App lifecycle deliveries `installation` and `installation_repositories`, and the `ping` handshake, are also supported. See [GitHub's event subscription documentation](https://docs.github.com/en/webhooks/webhook-events-and-payloads). Approve any changed permissions on existing installations manually.

Set a stable public HTTPS webhook URL ending in `/api/v1/webhooks/github`; enable delivery and use JSON. The frontend URL is not the webhook URL. Use a reverse proxy with request limits and TLS. Configure the identical high-entropy webhook secret at GitHub and in `GITHUB_WEBHOOK_SECRET`. Review GitHub delivery history for failed deliveries and redeliver after resolving configuration problems. No code in this repository remotely configures the App.

Configure `GITHUB_APP_ID` and `GITHUB_APP_PRIVATE_KEY_PATH`. The path must be absolute and point to a regular private-key file outside the checkout; restrict filesystem access to the backend/worker service account. Never print or check in keys. A missing file disables live App operations while mocked tests and independent APIs continue to work. Existing OAuth variables remain required for sign-in. Invalid local `DEBUG` must be corrected manually to a boolean; tests override it safely without changing `.env`.

## Database and workers

From `backend/`, with the existing virtual environment activated:

```powershell
python -m alembic upgrade head
python -m alembic current
python -m alembic check
python -m app.cli.sync_github_installations
python -m app.cli.verify_local_state
python -m app.cli.process_webhook_jobs --once
python -m app.cli.process_review_jobs --once
```

Omit `--once` to poll continuously. Run each worker as a supervised service with restart on failure and graceful termination. `--once` processes at most one eligible job, including a retryable job whose delay has expired. An empty queue exits successfully. Workers do not queue reviews for all historical PRs. Only opened/reopened/synchronize webhook deliveries matching an open PR's current SHA, or an authenticated manual request, queue a review. Completed reviews for that SHA are reused. Existing manual static-review CLI remains available.

After resolving a terminal job failure, list safe job IDs with `python -m app.cli.retry_job --kind webhook` (or `review`) and explicitly requeue one with `--job-id <uuid>`. This resets its bounded retry budget; completed/active jobs are unchanged. GitHub redelivery of an already persisted delivery is deduplicated and cannot restart a terminal job by itself. The original authenticated webhook record remains available for this local retry.

`JOB_TIMEOUT_SECONDS` defaults to 240; `JOB_LEASE_SECONDS` defaults to 300 and must exceed the timeout. `JOB_MAX_ATTEMPTS` defaults to 3 and cannot exceed 5. Claims use PostgreSQL `FOR UPDATE SKIP LOCKED`; session advisory locks prevent an alive stale worker from overlapping another worker for the same PR/job. Completion checks a random lease token. Expired leases recover automatically, and final expired attempts become failed. Retries have bounded exponential delays. Errors exposed to clients are fixed safe messages. Monitor failed/retryable job counts and investigate server-side service availability without logging payloads or credentials.

Cancellation waits for an already running trusted analyzer's bounded subprocess timeout before removing temporary files. Allow service shutdown enough time for this cleanup (up to the configured analyzer timeout); the advisory lock remains held until cleanup completes. The existing analyzer environment excludes application secrets.

Authenticated raw webhook records are retained for retries in `webhook_events`; they are never exposed by activity APIs. Activity is a minimal allowlisted projection. REST commits remain commits; only actual signed push deliveries create push activity. Static analysis uses bounded downloads, existing analyzer/path/size protections and temporary directories, and never executes PR code. Broad repository refreshes occur in workers, not webhook HTTP requests. Large repository refreshes can hit the configured job timeout and retry.

## Account isolation

Personal installation ownership is matched by verified GitHub user ID. Organization installation access requires an explicit local administrator grant; allowlisting a login does not grant access to other installations. After synchronizing the organization installation and after the user has logged in:

```powershell
python -m app.cli.grant_installation_access --user-github-id <numeric-user-id> --installation-github-id <numeric-installation-id>
```

Add `--revoke` to revoke this local grant. This CLI does not alter GitHub permissions. Scope is enforced on repository, PR, Issue, Commit, Review, Finding, Activity, Settings and dashboard reads. Legacy personal repositories receive a migration-time owner grant to preserve access before App setup; once installation access exists, its revocation takes precedence over the legacy grant. Organization membership discovery is not automatic.

## Cookies and deployment

Set `APP_ENV=production`, `DEBUG=false`, `AUTH_COOKIE_SECURE=true`, and explicit `AUTH_ALLOWED_GITHUB_LOGINS`. Configure the HTTPS `FRONTEND_URL` and exact OAuth callback URL. Sessions use HttpOnly cookies and existing SameSite protection. Keep the browser and mutation proxy on the same origin; the proxy rejects missing/mismatched Origin and forwards only the backend session cookie. New backend POST controls require exact configured frontend Origin. Do not cache authenticated responses at a reverse proxy. Apply database migrations before deploying code that reads new tables.

Use separate supervised services for FastAPI, Next.js, webhook workers and review workers. Set trusted proxy handling, restrictive database credentials, durable PostgreSQL storage, and a clean temporary directory with adequate quotas. The backend/database must be reachable by the Next.js server. Do not use temporary tunnel URLs for permanent delivery. No deployment or external resources are created by implementation work.

## Backups, rate limits and rotation

Use PostgreSQL tools matching the server's major version. Supply credentials through a protected PostgreSQL service definition or `.pgpass`, never shell command arguments or source control:

```powershell
pg_dump --dbname=service=ai_review --format=custom --file=review-backup.dump
pg_restore --dbname=service=ai_review_restore --no-owner review-backup.dump
```

Restore to a separate empty database, verify counts, migrated schema, review/finding links and worker queues, then test recovery before switching production. Restrict and encrypt backups: authenticated webhook records, issue text and session metadata are private. Test restoration periodically. Do not clear queues or overwrite the active database during a restore rehearsal.

Keep full synchronization serialized across API, CLI and workers using its database advisory lock. Avoid repeated manual syncs while workers are catching up. Existing GitHub clients honor request timeouts, retries and rate-limit responses; account for installation-specific quotas and GitHub secondary limits. See [GitHub rate-limit guidance](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).

Rotate App private keys by provisioning a new file, updating the protected service configuration, restarting workers, testing a sync, then revoking the old key. Rotate webhook secrets in a coordinated maintenance window; this endpoint accepts one configured secret. Update GitHub and backend together and redeliver interrupted deliveries. Rotate OAuth client secrets separately and revoke sessions when an incident requires it. Never store generated JWTs or installation tokens permanently.

## Release checklist

- Back up PostgreSQL and rehearse restoration.
- Run hermetic backend tests and frontend npm ci/test/lint/TypeScript/build.
- Resolve audited dependency vulnerabilities before deployment. The restored lockfile currently reports Next.js critical and brace-expansion high advisories; implementation work did not upgrade the pinned dependencies.
- Apply migrations and verify `alembic check` has no drift.
- Verify safe boolean App/key/webhook readiness and install permissions.
- Synchronize twice and compare UUIDs/counts plus PR/review fingerprints.
- Enable stable HTTPS delivery and manually verify a real ping and an authorized PR update.
- Start both workers; verify queue progress and safe failure/recovery.
- Grant only necessary organization installations to approved users.
- Confirm cross-account isolation, secure cookies, TLS and no shared caching.
- Monitor database availability, failed jobs, stale leases, disk quotas, rate limits and backups.

Live synchronization and delivery verification require a valid key and configured public URL. Historical activity cannot be reconstructed as push events. Automated tests use mocked GitHub services and safe synthetic configuration; they never depend on a live App.
