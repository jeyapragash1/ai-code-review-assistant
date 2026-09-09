"use client";
import { useState } from "react";
import { CodeXml, ThumbsDown, ThumbsUp } from "lucide-react";
import type { ReviewFinding } from "@/types";
import { Badge, Button, Card, EmptyState, Select } from "@/components/ui";
import { label } from "@/lib/utils";
import { SEVERITIES } from "@/lib/constants";
export function FindingCard({ finding: f }: { finding: ReviewFinding }) {
  const [feedback, setFeedback] = useState("");
  return (
    <Card className="scroll-mt-5">
      <article id={f.id}>
        <div className="panel-head">
          <div className="flex flex-wrap gap-2">
            <Badge tone={f.severity}>{label(f.severity)}</Badge>
            <Badge>{f.category}</Badge>
            <Badge>{f.source}</Badge>
          </div>
          <span className="muted text-xs">{f.confidence}% confidence</span>
        </div>
        <div className="space-y-4 p-5">
          <h3 className="text-base font-semibold">{f.title}</h3>
          <p className="muted flex items-start gap-2 break-all font-mono text-xs">
            <CodeXml size={14} className="shrink-0" />
            {f.file}:{f.startLine}-{f.endLine}
          </p>
          <div className="grid gap-4 lg:grid-cols-2">
            <div>
              <h4 className="mb-1 text-xs font-semibold">Problem</h4>
              <p className="muted text-sm leading-relaxed">{f.problem}</p>
            </div>
            <div>
              <h4 className="mb-1 text-xs font-semibold">Why it matters</h4>
              <p className="muted text-sm leading-relaxed">{f.impact}</p>
            </div>
          </div>
          <pre
            className="code-preview"
            tabIndex={0}
            aria-label={`Code excerpt from ${f.file}`}
          >
            <code>{f.snippet}</code>
          </pre>
          <div className="border-l-2 border-[var(--accent)] pl-4">
            <h4 className="mb-1 text-xs font-semibold accent">
              Suggested improvement
            </h4>
            <p className="muted text-sm leading-relaxed">{f.suggestion}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2 border-t border-[var(--border)] pt-4">
            <span className="muted mr-auto text-xs">
              Was this finding useful?
            </span>
            <Button
              onClick={() =>
                setFeedback(
                  "Helpful selected locally. Feedback was not submitted.",
                )
              }
              aria-label="Mark finding helpful (demo)"
            >
              <ThumbsUp size={13} />
              Helpful
            </Button>
            <Button
              className="icon-button"
              aria-label="Mark finding not helpful (demo)"
              title="Not helpful (demo)"
              onClick={() =>
                setFeedback(
                  "Not helpful selected locally. Feedback was not submitted.",
                )
              }
            >
              <ThumbsDown size={13} />
            </Button>
            <Badge>Demo only</Badge>
          </div>
          {feedback && (
            <p role="status" className="muted text-xs">
              {feedback}
            </p>
          )}
        </div>
      </article>
    </Card>
  );
}
export function FindingList({ findings }: { findings: ReviewFinding[] }) {
  const [severity, setSeverity] = useState("all");
  const [category, setCategory] = useState("all");
  const filtered = findings.filter(
    (f) =>
      (severity === "all" || f.severity === severity) &&
      (category === "all" || f.category === category),
  );
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="section-title">
          Findings <span className="muted ml-1">({findings.length})</span>
        </h2>
        <div className="grid w-full grid-cols-2 gap-3 sm:w-auto">
          <Select
            label="Severity"
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
          >
            <option value="all">All severities</option>
            {SEVERITIES.map((s) => (
              <option key={s} value={s}>
                {label(s)}
              </option>
            ))}
          </Select>
          <Select
            label="Category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="all">All categories</option>
            {[...new Set(findings.map((f) => f.category))].map((c) => (
              <option key={c}>{c}</option>
            ))}
          </Select>
        </div>
      </div>
      {filtered.map((f) => (
        <FindingCard key={f.id} finding={f} />
      ))}
      {!filtered.length && (
        <EmptyState
          title={
            findings.length
              ? "No matching findings"
              : "No findings in this review"
          }
          description={
            findings.length
              ? "Adjust the severity or category filter."
              : "Always verify the code independently before merging."
          }
        />
      )}
    </section>
  );
}
