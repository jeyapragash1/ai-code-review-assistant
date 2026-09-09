import type {
  DashboardStatistics,
  PullRequest,
  Repository,
  Review,
  ReviewActivityPoint,
  ReviewFinding,
  Severity,
} from "@/types";

export const repositories: Repository[] = [
  {
    id: "atlas-api",
    owner: "acme",
    name: "atlas-api",
    description: "Core services for the Atlas commerce platform.",
    language: "Python",
    defaultBranch: "main",
    isActive: true,
  },
  {
    id: "console",
    owner: "acme",
    name: "console",
    description: "The workspace for teams building on Atlas.",
    language: "TypeScript",
    defaultBranch: "main",
    isActive: true,
  },
  {
    id: "event-pipeline",
    owner: "acme",
    name: "event-pipeline",
    description: "Reliable event delivery and stream processing.",
    language: "Go",
    defaultBranch: "main",
    isActive: true,
  },
  {
    id: "design-system",
    owner: "acme",
    name: "design-system",
    description: "Shared components, tokens, and design foundations.",
    language: "TypeScript",
    defaultBranch: "main",
    isActive: false,
  },
];
const sha = "a8f3c21d9e4b60578f12a6cd34e901bc782da564";
export const pullRequests: PullRequest[] = [
  {
    id: "pr-142",
    repositoryId: "atlas-api",
    number: 142,
    title: "Add workspace member search",
    author: "maya-chen",
    baseBranch: "main",
    headBranch: "feat/member-search",
    status: "open",
    headSha: sha,
    filesChanged: 8,
    additions: 246,
    deletions: 38,
  },
  {
    id: "pr-89",
    repositoryId: "console",
    number: 89,
    title: "Validate project creation form",
    author: "alex-rivera",
    baseBranch: "main",
    headBranch: "feat/project-form",
    status: "open",
    headSha: "b71e982ce065de7490837ac1f2e6a9d01034bc25",
    filesChanged: 5,
    additions: 128,
    deletions: 24,
  },
  {
    id: "pr-56",
    repositoryId: "event-pipeline",
    number: 56,
    title: "Improve delivery retry handling",
    author: "sam-patel",
    baseBranch: "main",
    headBranch: "fix/retry-policy",
    status: "merged",
    headSha: "c4d97f1e6ba0372d098514fcee6a13278b942d50",
    filesChanged: 3,
    additions: 82,
    deletions: 16,
  },
  {
    id: "pr-87",
    repositoryId: "console",
    number: 87,
    title: "Simplify permission state selectors",
    author: "alex-rivera",
    baseBranch: "main",
    headBranch: "refactor/permissions",
    status: "merged",
    headSha: "d829a46eb2f719a93085cd124670be8a4c2d351f",
    filesChanged: 4,
    additions: 42,
    deletions: 96,
  },
  {
    id: "pr-32",
    repositoryId: "design-system",
    number: 32,
    title: "Normalize button focus states",
    author: "maya-chen",
    baseBranch: "main",
    headBranch: "fix/focus-states",
    status: "closed",
    headSha: "e91bc52d834716fba248907cdaab3127658fe940",
    filesChanged: 2,
    additions: 26,
    deletions: 12,
  },
  {
    id: "pr-143",
    repositoryId: "atlas-api",
    number: 143,
    title: "Introduce cursor pagination",
    author: "sam-patel",
    baseBranch: "main",
    headBranch: "feat/cursor-pagination",
    status: "open",
    headSha: "f216a45d79b138e00a7c6524debf9384c1a05267",
    filesChanged: 6,
    additions: 184,
    deletions: 51,
  },
];
export const reviews: Review[] = [
  {
    id: "rev-1048",
    pullRequestId: "pr-142",
    status: "completed",
    summary:
      "Two security issues need attention before merging. Member search interpolates user input into SQL, and the export route does not verify workspace membership. Parameterize the query and enforce authorization at the route boundary.",
    createdAt: "2026-09-09T10:42:00Z",
    commitSha: sha,
    staticSeconds: 4.2,
    aiSeconds: 14.6,
  },
  {
    id: "rev-1047",
    pullRequestId: "pr-89",
    status: "completed",
    summary:
      "The form is well structured, but project names need server-side length validation. Client-side validation alone does not protect the API boundary.",
    createdAt: "2026-09-08T15:20:00Z",
    commitSha: pullRequests[1].headSha,
    staticSeconds: 2.8,
    aiSeconds: 10.4,
  },
  {
    id: "rev-1046",
    pullRequestId: "pr-56",
    status: "completed",
    summary:
      "Retry handling is clearer. Preserve error context when a delivery fails so operators can distinguish transient failures from invalid requests.",
    createdAt: "2026-09-07T09:12:00Z",
    commitSha: pullRequests[2].headSha,
    staticSeconds: 3.1,
    aiSeconds: 11.2,
  },
  {
    id: "rev-1045",
    pullRequestId: "pr-87",
    status: "completed",
    summary:
      "A focused refactor with no security findings. Extract repeated permission predicates to keep future changes consistent.",
    createdAt: "2026-09-06T11:05:00Z",
    commitSha: pullRequests[3].headSha,
    staticSeconds: 2.1,
    aiSeconds: 8.3,
  },
  {
    id: "rev-1044",
    pullRequestId: "pr-32",
    status: "completed",
    summary:
      "No findings in this review. Focus indicators are consistent across button variants and preserve keyboard visibility.",
    createdAt: "2026-09-05T14:30:00Z",
    commitSha: pullRequests[4].headSha,
    staticSeconds: 1.9,
    aiSeconds: 7.1,
  },
  {
    id: "rev-1049",
    pullRequestId: "pr-143",
    status: "processing",
    summary:
      "Analysis is in progress in this demo snapshot. Findings and risk are not available yet.",
    createdAt: "2026-09-09T11:00:00Z",
    commitSha: pullRequests[5].headSha,
    staticSeconds: 3.2,
    aiSeconds: 0,
  },
  {
    id: "rev-1043",
    pullRequestId: "pr-142",
    status: "failed",
    summary:
      "Analysis did not complete for the previous commit. No findings were produced. The newer review completed successfully.",
    createdAt: "2026-09-04T10:00:00Z",
    commitSha: "072bf813d9a4c1e6659ab10823f6de7a480c5192",
    staticSeconds: 2.4,
    aiSeconds: 0,
  },
];
export const findings: ReviewFinding[] = [
  {
    id: "finding-1",
    reviewId: "rev-1048",
    severity: "high",
    category: "Security",
    source: "Hybrid",
    file: "app/api/members.py",
    startLine: 42,
    endLine: 44,
    title: "User input interpolated into SQL query",
    problem:
      "The search parameter is inserted directly into the SQL statement. A crafted input can change the query structure.",
    impact:
      "An attacker could access records outside the intended search or modify database contents with the application role's privileges.",
    suggestion:
      "Use bound parameters for the search value. Keep the SQL structure static and apply workspace scoping before executing the query.",
    confidence: 98,
    snippet:
      "42  query = f\"SELECT * FROM members WHERE name = '{search}'\"\n43  result = await session.execute(text(query))\n44  return result.all()",
  },
  {
    id: "finding-2",
    reviewId: "rev-1048",
    severity: "high",
    category: "Security",
    source: "AI",
    file: "app/api/exports.py",
    startLine: 28,
    endLine: 30,
    title: "Workspace export missing authorization check",
    problem:
      "The route checks that a user is signed in but does not verify membership in the requested workspace.",
    impact:
      "An authenticated user could export another workspace's member data by changing the workspace identifier.",
    suggestion:
      "Require a workspace membership and export permission check before loading data. Add tests for users from a different workspace.",
    confidence: 94,
    snippet:
      "28  async def export_members(workspace_id, current_user):\n29      members = await load_members(workspace_id)\n30      return build_export(members)",
  },
  {
    id: "finding-3",
    reviewId: "rev-1047",
    severity: "medium",
    category: "Validation",
    source: "Hybrid",
    file: "src/app/api/projects/route.ts",
    startLine: 16,
    endLine: 18,
    title: "Project name lacks input validation",
    problem:
      "The API accepts the request's name without validating its type, length, or whitespace-only values.",
    impact:
      "Malformed names may cause database errors and inconsistent project labels, even when the browser form validates input.",
    suggestion:
      "Validate the request at the server boundary. Require a trimmed non-empty string with a documented maximum length.",
    confidence: 97,
    snippet:
      "16  const body = await request.json();\n17  const project = await createProject(body.name);\n18  return Response.json(project);",
  },
  {
    id: "finding-4",
    reviewId: "rev-1046",
    severity: "medium",
    category: "Reliability",
    source: "Static Analysis",
    file: "internal/delivery/worker.go",
    startLine: 73,
    endLine: 75,
    title: "Delivery error loses diagnostic context",
    problem:
      "All delivery errors are replaced by the same message, discarding the cause and retry classification.",
    impact:
      "Operators cannot distinguish permanent failures from temporary network errors, making recovery slower and retries less precise.",
    suggestion:
      "Wrap the error with safe operational context and preserve the cause. Avoid including payloads or credentials in error strings.",
    confidence: 91,
    snippet:
      '73  if err != nil {\n74      return errors.New("delivery failed")\n75  }',
  },
  {
    id: "finding-5",
    reviewId: "rev-1045",
    severity: "low",
    category: "Maintainability",
    source: "AI",
    file: "src/lib/permissions.ts",
    startLine: 34,
    endLine: 36,
    title: "Repeated permission predicates may drift",
    problem: "The same role predicate is repeated across multiple selectors.",
    impact:
      "A future role change may update one selector while leaving another with inconsistent access behavior.",
    suggestion:
      "Extract a named predicate and cover the role matrix with focused tests.",
    confidence: 86,
    snippet:
      '34  const canEdit = role === "owner" || role === "admin";\n35  const canInvite = role === "owner" || role === "admin";\n36  const canManage = role === "owner" || role === "admin";',
  },
];
export const getRepository = (id: string) =>
  repositories.find((r) => r.id === id);
export const getPullRequest = (id: string) =>
  pullRequests.find((p) => p.id === id);
export const getReview = (id: string) => reviews.find((r) => r.id === id);
export const reviewFindings = (id: string) =>
  findings.filter((f) => f.reviewId === id);
export const prReviews = (id: string) =>
  reviews
    .filter((r) => r.pullRequestId === id)
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
export const repoPRs = (id: string) =>
  pullRequests.filter((p) => p.repositoryId === id);
export const repoReviews = (id: string) =>
  reviews.filter((r) => repoPRs(id).some((p) => p.id === r.pullRequestId));
export const repoFindings = (id: string) =>
  findings.filter((f) => repoReviews(id).some((r) => r.id === f.reviewId));
export function risk(items: ReviewFinding[]): Severity | "clear" {
  return items.some((f) => f.severity === "high")
    ? "high"
    : items.some((f) => f.severity === "medium")
      ? "medium"
      : items.length
        ? "low"
        : "clear";
}
export const reviewRisk = (r: Review) =>
  r.status === "completed" ? risk(reviewFindings(r.id)) : "pending";
export const statistics: DashboardStatistics = {
  repositories: repositories.filter((r) => r.isActive).length,
  reviewedPullRequests: new Set(
    reviews.filter((r) => r.status === "completed").map((r) => r.pullRequestId),
  ).size,
  findings: findings.length,
  highSeverityFindings: findings.filter((f) => f.severity === "high").length,
};
export function activityFor(items: Review[] = reviews): ReviewActivityPoint[] {
  return [
    "2026-09-03",
    "2026-09-04",
    "2026-09-05",
    "2026-09-06",
    "2026-09-07",
    "2026-09-08",
    "2026-09-09",
  ].map((date) => {
    const day = items.filter(
      (r) => r.createdAt.startsWith(date) && r.status === "completed",
    );
    return {
      date: `Sep ${Number(date.slice(-2))}`,
      reviews: day.length,
      findings: day.reduce((sum, r) => sum + reviewFindings(r.id).length, 0),
    };
  });
}
