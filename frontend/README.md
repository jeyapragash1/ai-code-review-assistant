# CodeReview AI

Responsive Next.js 16 dashboard displaying real PostgreSQL data through the FastAPI read APIs. No runtime mock repositories, Pull Requests, reviews, findings, risk scores, or activity charts remain. Dark, light, and system themes are supported.

## Run locally

Start PostgreSQL, then synchronize GitHub and start FastAPI in PowerShell:

```powershell
cd C:\Users\Admin\OneDrive\Desktop\ai-code-review-assistant\backend
.\.venv\Scripts\python.exe -m app.cli.sync_repository
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second PowerShell window:

```powershell
cd C:\Users\Admin\OneDrive\Desktop\ai-code-review-assistant\frontend
npm ci
npm run dev
```

Open http://localhost:3000. Stop each server with Ctrl+C. Synchronization is administrative and CLI-only; the frontend refresh button only reloads already stored backend data. The frontend never calls GitHub directly.

## Configuration

The safe default is also documented in `.env.local.example`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

No local environment file is needed for this default. A different deployment can configure this public value; it must be an HTTP(S) base URL without credentials, query parameters, or a fragment. Never put tokens or secrets in public environment variables. Settings displays only the URL origin. The API must be reachable from the Next.js server, not only from the user's browser.

## Architecture

- `src/types`: response types matching backend Pydantic schemas, including nullable fields and backend pagination.
- `src/lib/api/client.ts`: native GET fetch, encoded URL construction, five-second timeout, no credentials, no caching, and safe error mapping. No automatic retries or polling.
- `src/lib/api/parsers.ts`: runtime validation of untrusted JSON into typed response objects.
- `src/lib/api/{dashboard,repositories,pull-requests}.ts`: endpoint-specific transport functions.
- `src/lib/api/server.ts`: Server Component data loading and request-scoped dashboard deduplication. Next.js `connection()` defers API access until a request, so production builds do not need FastAPI.
- `src/app/(dashboard)`: server-rendered pages and a template that refreshes connectivity on navigation. Only a successful dashboard request enables the Live API indicator.
- `src/components`: reusable responsive shell, real repository/PR lists, filters, pagination, safe error/empty states, refresh button, and theme preferences.

Search, filters, page size, and page are encoded in URL query parameters. Native GET filter forms reset to page 1. Previous/next links preserve filters and use backend totals; data is never paginated locally. UTC timestamp formatting handles missing timestamps explicitly. Native dialogs, semantic forms, visible focus rings, accessible control labels, and reduced-motion styles are retained.

## Routes

| Route                 | Data / behaviour                                     |
| --------------------- | ---------------------------------------------------- |
| `/`                   | Redirect to dashboard                                |
| `/dashboard`          | Real statistics and recently updated PRs             |
| `/repositories`       | Paginated search and active-state filtering          |
| `/repositories/[id]`  | Database UUID, repository metadata and real PR page  |
| `/pull-requests`      | Paginated search, repository and status filtering    |
| `/pull-requests/[id]` | Real PR metadata and change counts                   |
| `/reviews`            | Honest unavailable feature state                     |
| `/reviews/[id]`       | Not found; no mock review IDs accepted               |
| `/settings`           | Local theme, API connectivity, real repository count |

The six consumed endpoints are `/dashboard/statistics`, `/repositories`, `/repositories/{id}`, `/repositories/{id}/pull-requests`, `/pull-requests`, and `/pull-requests/{id}`, relative to the API base. Unknown/invalid detail IDs show the not-found page. Reviews and findings have no backend implementation yet; dashboard zeros come from the backend, and no analysis is fabricated. Authentication, AI configuration, notifications, and GitHub App installation are not configured by this UI.

## Verification

Use Node.js 24 for the lightweight built-in test runner with TypeScript stripping:

```powershell
npm test
npm run lint
npx tsc --noEmit
npm run build
npm run start
```

Tests exercise URL construction, pagination, typed response validation, safe transport errors, credential omission, and rejection of mock IDs. They mock fetch and do not require GitHub or FastAPI. Production builds must succeed with FastAPI stopped; runtime pages remain dynamic. The production server defaults to http://localhost:3000.

## Troubleshooting

If FastAPI is stopped or PostgreSQL is unavailable, the shell remains usable and data pages display API unavailable with refresh and startup guidance. There is no fallback to mock data. Start the backend with the command above, then Refresh. A successful repository sync does not manufacture PRs: a repository with no GitHub PRs correctly displays an empty list. Validation failures and unexpected errors have separate safe messages; raw backend errors are never shown.

Theme preference alone persists locally in the browser. No settings are submitted to the backend. Real GitHub synchronization and private backend configuration remain outside the frontend.
