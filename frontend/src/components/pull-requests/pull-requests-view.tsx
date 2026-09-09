"use client";
import { useState } from "react";
import {
  prReviews,
  pullRequests,
  repositories,
  reviewRisk,
} from "@/lib/mock-data";
import {
  Button,
  Card,
  EmptyState,
  Input,
  PageHeading,
  Select,
} from "@/components/ui";
import { PullRequestList } from "./pull-request-list";
export function PullRequestsView() {
  const [search, setSearch] = useState("");
  const [repo, setRepo] = useState("all");
  const [status, setStatus] = useState("all");
  const [risk, setRisk] = useState("all");
  const filtered = pullRequests.filter((p) => {
    const latest = prReviews(p.id)[0];
    return (
      `${p.title} ${p.number} ${p.author}`
        .toLowerCase()
        .includes(search.toLowerCase()) &&
      (repo === "all" || p.repositoryId === repo) &&
      (status === "all" || p.status === status) &&
      (risk === "all" || (latest ? reviewRisk(latest) : "pending") === risk)
    );
  });
  return (
    <div className="page-stack">
      <PageHeading
        title="Pull Requests"
        description="Follow changes across repositories and see where a closer look is needed."
      />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-[2fr_1fr_1fr_1fr]">
        <Input
          label="Search pull requests"
          placeholder="Title, PR number, or author..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <Select
          label="Repository"
          value={repo}
          onChange={(e) => setRepo(e.target.value)}
        >
          <option value="all">All repositories</option>
          {repositories.map((r) => (
            <option key={r.id} value={r.id}>
              {r.owner}/{r.name}
            </option>
          ))}
        </Select>
        <Select
          label="Status"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="all">All statuses</option>
          <option value="open">Open</option>
          <option value="closed">Closed</option>
          <option value="merged">Merged</option>
        </Select>
        <Select
          label="Risk"
          value={risk}
          onChange={(e) => setRisk(e.target.value)}
        >
          <option value="all">All risk levels</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="clear">No findings</option>
          <option value="pending">Not assessed</option>
        </Select>
      </div>
      <p className="muted text-xs" aria-live="polite">
        {filtered.length} of {pullRequests.length} pull requests
      </p>
      <Card>
        {filtered.length ? (
          <PullRequestList items={filtered} />
        ) : (
          <EmptyState>
            <Button
              onClick={() => {
                setSearch("");
                setRepo("all");
                setStatus("all");
                setRisk("all");
              }}
            >
              Clear filters
            </Button>
          </EmptyState>
        )}
      </Card>
    </div>
  );
}
