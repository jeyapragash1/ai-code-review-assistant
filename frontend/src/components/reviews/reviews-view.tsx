"use client";
import { useState } from "react";
import {
  getPullRequest,
  repositories,
  reviews,
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
import { ReviewList } from "./review-list";
export function ReviewsView() {
  const [search, setSearch] = useState("");
  const [repo, setRepo] = useState("all");
  const [status, setStatus] = useState("all");
  const [risk, setRisk] = useState("all");
  const filtered = [...reviews]
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
    .filter((r) => {
      const p = getPullRequest(r.pullRequestId);
      return (
        p &&
        `${p.title} ${p.number} ${r.id}`
          .toLowerCase()
          .includes(search.toLowerCase()) &&
        (repo === "all" || p.repositoryId === repo) &&
        (status === "all" || r.status === status) &&
        (risk === "all" || reviewRisk(r) === risk)
      );
    });
  return (
    <div className="page-stack">
      <PageHeading
        title="Reviews"
        description="Explore analysis results, understand risks, and review suggested improvements."
      />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-[2fr_1fr_1fr_1fr]">
        <Input
          label="Search reviews"
          placeholder="PR title, number, or review ID..."
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
            <option value={r.id} key={r.id}>
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
          <option value="completed">Completed</option>
          <option value="processing">Processing</option>
          <option value="failed">Failed</option>
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
        {filtered.length} of {reviews.length} reviews
      </p>
      <Card>
        {filtered.length ? (
          <ReviewList items={filtered} />
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
