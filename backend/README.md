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

The API documentation is available at:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`
- `http://127.0.0.1:8000/openapi.json`

## Test

```powershell
python -m pytest
```

## Database

The backend uses SQLAlchemy 2 async sessions with Psycopg 3. FastAPI disposes database connections during application shutdown.

The first GitHub ingestion tables are:

- `repositories`: stores synchronized GitHub repository identity and display metadata. It does not store GitHub tokens or secrets.
- `pull_requests`: stores pull request identity and review-target metadata for a repository. Pull requests are deleted when their stored repository is deleted.
- `webhook_events`: stores unique GitHub webhook deliveries for later asynchronous processing and retry support.

Webhook payloads may contain sensitive metadata. Do not log, print, or expose raw webhook payload contents.

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
