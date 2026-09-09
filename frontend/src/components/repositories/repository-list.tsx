"use client";
import Link from "next/link";
import { useState } from "react";
import { ArrowUpRight, FolderGit2, GitBranch, Plus } from "lucide-react";
import {
  repositories,
  repoFindings,
  repoPRs,
  repoReviews,
  risk,
} from "@/lib/mock-data";
import { formatDate } from "@/lib/utils";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Input,
  PageHeading,
  Select,
  SeverityBadge,
  StatusBadge,
} from "@/components/ui";
export function RepositoryList() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [message, setMessage] = useState(false);
  const filtered = repositories.filter(
    (r) =>
      `${r.owner}/${r.name}`.toLowerCase().includes(search.toLowerCase()) &&
      (status === "all" || r.isActive === (status === "active")),
  );
  return (
    <div className="page-stack">
      <PageHeading
        title="Repositories"
        description="Track code quality across your connected repositories."
        action={
          <Button className="primary" onClick={() => setMessage(true)}>
            <Plus size={16} />
            Connect repository
          </Button>
        }
      />
      {message && (
        <p role="status" className="bordered rounded-md p-4 text-sm muted">
          Repository connections are unavailable in demo mode. No connection has
          been created.
        </p>
      )}
      <div className="grid gap-3 sm:grid-cols-[1fr_180px]">
        <Input
          label="Search repositories"
          placeholder="Search by owner or repository name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <Select
          label="Status"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="all">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </Select>
      </div>
      <p className="muted text-xs" aria-live="polite">
        {filtered.length} of {repositories.length} repositories
      </p>
      <div className="grid gap-5 lg:grid-cols-2">
        {filtered.map((r) => {
          const rs = repoReviews(r.id).sort((a, b) =>
            b.createdAt.localeCompare(a.createdAt),
          );
          const completed = new Set(
            rs
              .filter((v) => v.status === "completed")
              .map((v) => v.pullRequestId),
          ).size;
          return (
            <Card key={r.id}>
              <div className="p-5">
                <div className="mb-4 flex items-center justify-between">
                  <span className="subtle rounded-md p-2.5">
                    <FolderGit2 size={22} className="accent" />
                  </span>
                  <StatusBadge status={r.isActive ? "active" : "inactive"} />
                </div>
                <Link
                  className="break-safe text-base font-semibold hover:underline"
                  href={`/repositories/${r.id}`}
                >
                  {r.owner}
                  <span className="muted mx-1">/</span>
                  {r.name}
                </Link>
                <p className="muted mt-2 min-h-10 text-sm">{r.description}</p>
                <div className="mt-4 flex flex-wrap gap-4 text-xs muted">
                  <span className="flex items-center gap-1.5">
                    <span
                      className={`h-2 w-2 rounded-full ${r.language === "Python" ? "bg-amber-400" : r.language === "Go" ? "bg-teal-400" : "bg-blue-400"}`}
                    />
                    {r.language}
                  </span>
                  <span className="flex items-center gap-1">
                    <GitBranch size={12} />
                    {r.defaultBranch}
                  </span>
                  <Badge>{repoPRs(r.id).length} PRs</Badge>
                </div>
                <div className="mt-5 grid grid-cols-3 gap-3 border-t border-[var(--border)] pt-4">
                  <div>
                    <p className="text-lg font-semibold">{completed}</p>
                    <p className="muted text-[11px]">PRs reviewed</p>
                  </div>
                  <div>
                    <p className="text-lg font-semibold">
                      {repoFindings(r.id).length}
                    </p>
                    <p className="muted text-[11px]">Findings</p>
                  </div>
                  <div>
                    <SeverityBadge severity={risk(repoFindings(r.id))} />
                    <p className="muted mt-2 text-[11px]">Overall risk</p>
                  </div>
                </div>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[var(--border)] px-5 py-3">
                <span className="muted text-[11px]">
                  Latest review{" "}
                  {rs[0] ? formatDate(rs[0].createdAt) : "not available"}
                </span>
                <Link
                  href={`/repositories/${r.id}`}
                  className="accent flex items-center gap-1 text-xs"
                >
                  Details <ArrowUpRight size={14} />
                </Link>
              </div>
            </Card>
          );
        })}
      </div>
      {!filtered.length && (
        <EmptyState>
          <Button
            onClick={() => {
              setSearch("");
              setStatus("all");
            }}
          >
            Clear filters
          </Button>
        </EmptyState>
      )}
    </div>
  );
}
