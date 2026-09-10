import test from "node:test";
import assert from "node:assert/strict";
import { apiUrl, get } from "../src/lib/api/client.ts";
import { normalizeApiBase } from "../src/lib/config.ts";
import { ApiError, statusError } from "../src/lib/api/errors.ts";
import {
  paginationQuery,
  pageHref,
  activeQuery,
  statusQuery,
} from "../src/lib/api/filters.ts";
import {
  parseRepository,
  parsePage,
  parseDashboard,
  isUuid,
} from "../src/lib/api/parsers.ts";

const repository = {
  id: "00000000-0000-4000-8000-000000000001",
  github_repository_id: 1,
  owner: "test-owner",
  name: "test-repository",
  full_name: "test-owner/test-repository",
  html_url: null,
  description: null,
  default_branch: "main",
  primary_language: null,
  is_private: false,
  is_active: true,
  pull_request_count: 0,
  open_pull_request_count: 0,
  github_updated_at: null,
  last_synced_at: null,
  created_at: "2026-09-01T00:00:00Z",
  updated_at: "2026-09-01T00:00:00Z",
};

test("normalizes API base and rejects credential-bearing configuration", () => {
  assert.equal(
    normalizeApiBase(" http://127.0.0.1:8000/api/v1/// ").href,
    "http://127.0.0.1:8000/api/v1/",
  );
  for (const value of [
    "https://user:password@example.com/api",
    "file:///api",
    "https://example.com/api?token=test",
    "https://example.com/api#x",
  ])
    assert.throws(() => normalizeApiBase(value));
});
test("constructs encoded paths and pagination without query injection", () => {
  const url = apiUrl(
    ["repositories", "a/b"],
    { page: 2, page_size: 25, search: "a&is_active=true", is_active: false },
    new URL("http://localhost/api/v1/"),
  );
  assert.equal(url.pathname, "/api/v1/repositories/a%2Fb");
  assert.equal(url.searchParams.get("search"), "a&is_active=true");
  assert.equal(url.searchParams.get("is_active"), "false");
  assert.equal(url.searchParams.get("page"), "2");
  assert.equal(url.searchParams.get("page_size"), "25");
  assert.throws(() => apiUrl([".."]));
});
test("pagination preserves filters and rejects invalid or duplicate values", () => {
  assert.deepEqual(paginationQuery({}), { page: 1, page_size: 20 });
  for (const params of [
    { page: "0" },
    { page_size: "101" },
    { page: ["1", "2"] },
    { page: "NaN" },
  ])
    assert.throws(() => paginationQuery(params));
  const href = new URL(
    pageHref(
      "/repositories",
      { search: "a & b", is_active: false, page_size: 10 },
      2,
    ),
    "http://localhost",
  );
  assert.equal(href.searchParams.get("search"), "a & b");
  assert.equal(href.searchParams.get("page"), "2");
  assert.equal(activeQuery({ is_active: "false" }), false);
  assert.throws(() => statusQuery({ status: "reviewed" }));
});
test("validates repository and empty paginated success bodies", () => {
  assert.deepEqual(parseRepository(repository), repository);
  assert.throws(() =>
    parseRepository({ ...repository, pull_request_count: "0" }),
  );
  assert.throws(() =>
    parseRepository({ ...repository, updated_at: "invalid" }),
  );
  const empty = { items: [], total: 0, page: 1, page_size: 20, total_pages: 0 };
  assert.deepEqual(parsePage(empty, parseRepository), empty);
  assert.throws(() => parsePage({ ...empty, total_pages: 1 }, parseRepository));
});
test("dashboard preserves honest zero review and finding values", () => {
  const data = {
    connected_repository_count: 1,
    total_pull_request_count: 0,
    open_pr_count: 0,
    closed_pr_count: 0,
    merged_pr_count: 0,
    reviews_count: 0,
    findings_count: 0,
    high_severity_findings_count: 0,
    recently_updated_pull_requests: [],
  };
  assert.deepEqual(parseDashboard(data), data);
  assert.throws(() => parseDashboard({ ...data, reviews_count: 10 }));
});
test("mock IDs are not accepted as backend UUIDs", () => {
  for (const id of ["atlas-api", "pr-142", "rev-1048"])
    assert.equal(isUuid(id), false);
  assert.equal(isUuid(repository.id), true);
});
test("GET transport parses typed data and omits credentials", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    assert.equal(options.method, "GET");
    assert.equal(options.credentials, "omit");
    assert.equal(options.cache, "no-store");
    assert.equal(options.headers.Authorization, undefined);
    assert.equal(url.searchParams.get("page"), "1");
    return Response.json(repository);
  };
  try {
    assert.deepEqual(
      await get(["repositories"], parseRepository, { page: 1 }),
      repository,
    );
  } finally {
    globalThis.fetch = original;
  }
});
test("HTTP errors map safely without leaking backend body", async () => {
  const original = globalThis.fetch;
  try {
    for (const [status, kind] of [
      [404, "not_found"],
      [422, "validation"],
      [503, "unavailable"],
      [500, "unexpected"],
    ]) {
      assert.equal(statusError(status).kind, kind);
      globalThis.fetch = async () =>
        Response.json({ detail: "private-internal-error" }, { status });
      await assert.rejects(
        get(["repositories"], parseRepository),
        (error) =>
          error instanceof ApiError &&
          error.kind === kind &&
          !error.message.includes("private"),
      );
    }
  } finally {
    globalThis.fetch = original;
  }
});
test("network failure and malformed success have safe distinct errors", async () => {
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async () => {
      throw new Error("private-network-details");
    };
    await assert.rejects(get(["repositories"], parseRepository), {
      kind: "unavailable",
    });
    globalThis.fetch = async () => Response.json({ invalid: true });
    await assert.rejects(get(["repositories"], parseRepository), {
      kind: "unexpected",
    });
  } finally {
    globalThis.fetch = original;
  }
});
