# CodeReview AI

A responsive GitHub code review dashboard built with Next.js App Router, React, TypeScript, and Tailwind CSS. Dark mode is the default; light and system themes are supported.

## Run locally

From Windows PowerShell:

```powershell
cd C:\Users\Admin\OneDrive\Desktop\ai-code-review-assistant\frontend
npm ci
npm run dev
```

Open http://localhost:3000. Stop the server with Ctrl+C.

## Verification

```powershell
npm run lint
npx tsc --noEmit
npm run build
npm run start
```

The production server runs on http://localhost:3000. Stop it with Ctrl+C.

## Routes

| Route                 | Purpose                                                           |
| --------------------- | ----------------------------------------------------------------- |
| `/`                   | Redirects to `/dashboard`                                         |
| `/dashboard`          | Statistics, activity, severity, recent reviews, repository health |
| `/repositories`       | Search and filter repositories                                    |
| `/repositories/[id]`  | Repository activity, PRs, and findings                            |
| `/pull-requests`      | Search and filter PRs by repository, state, and risk              |
| `/pull-requests/[id]` | Changes, latest findings, and review history                      |
| `/reviews`            | Filterable review history                                         |
| `/reviews/[id]`       | Review summary, timings, severity, and detailed findings          |
| `/settings`           | Local demonstration preferences and theme                         |

Example detail paths: `/repositories/atlas-api`, `/pull-requests/pr-142`, and `/reviews/rev-1048`. Unknown IDs display a not-found view. `/reviews/rev-1049` demonstrates processing, `/reviews/rev-1043` demonstrates failure, and `/reviews/rev-1044` has no findings.

## Architecture

- `src/app`: server-rendered routes, dashboard layout, loading, error, and not-found boundaries.
- `src/components/layout`: responsive navigation, native-dialog mobile drawer, workspace search, notifications, and theme toggle.
- `src/components/ui`: buttons, badges, cards, inputs, selects, table, skeleton, empty state, stat cards, breadcrumbs, risk summary, and external links.
- `src/components/charts`: responsive Recharts activity and severity charts with deterministic data and textual summaries.
- Domain component folders: dashboard, repositories, pull-requests, reviews, findings, and settings.
- `src/types`: explicit domain interfaces and union types.
- `src/lib/mock-data.ts`: centralized fixtures and derived selectors.
- `src/lib/constants.ts`: product details and future API base configuration.
- `src/providers`: next-themes provider.

Client components are used for filters, dialogs, local preferences, feedback, and chart rendering. Route lookup and detail composition remain Server Components. Chart dimensions are fixed responsively; animations are disabled. Native dialogs support Escape, focus containment, and focus restoration. Focus rings, labeled controls, text severity labels, and reduced-motion styles support accessibility.

## Mock data

All repository, pull request, review, and finding relationships use stable IDs. Counts, risk levels, and activity are computed from the same collections. Dates are a fixed September 2026 snapshot formatted in UTC. A processing or failed review is marked not assessed rather than clear. Repository risk summarizes all stored findings; PR risk uses its latest review. Successful review count includes only completed analyses.

Repositories and contributors are fictional. Their external links open GitHub search, not an invented repository or pull request URL. The sidebar links to the real project repository. Insecure sample code exists only as escaped text in finding previews and is never executed.

Connecting repositories is unavailable. Feedback reports local selection without submission. Review and notification preferences are temporary local state and do not affect the fixture snapshot. Theme preference alone persists in browser storage. No authentication or network-backed operations are implemented.

## Environment

`frontend/.env.local.example` documents the future configuration:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

`API_BASE_URL` has this same fallback. It is intentionally not used for HTTP requests yet. Real `.env.local` files remain ignored. Never put secrets in `NEXT_PUBLIC_` variables because they are public browser configuration.

Backend integration, live GitHub data, AI calls, authentication, and server settings persistence are intentionally deferred.
