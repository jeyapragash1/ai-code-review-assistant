import Link from "next/link";
import { CloudOff, CircleAlert } from "lucide-react";
import type { ApiErrorKind } from "@/lib/api/errors";
import { RefreshButton } from "./refresh-button";
export function ApiState({ kind }: { kind: ApiErrorKind }) {
  const title =
    kind === "unavailable"
      ? "API unavailable"
      : kind === "validation"
        ? "Check your filters"
        : kind === "not_found"
          ? "Record not found"
          : "Unable to load backend data";
  return (
    <section
      role="alert"
      className="panel flex flex-col items-center gap-4 px-5 py-12 text-center"
    >
      {kind === "unavailable" ? (
        <CloudOff size={32} className="muted" />
      ) : (
        <CircleAlert size={32} className="muted" />
      )}
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="muted max-w-lg text-sm">
        {kind === "unavailable"
          ? "Start FastAPI and make sure PostgreSQL is running, then refresh this page. No sample data is being shown."
          : kind === "validation"
            ? "Use a valid page number, page size from 1 to 100, and supported filter values."
            : "The requested data could not be loaded. Refresh to try again."}
      </p>
      {kind === "unavailable" && (
        <div className="max-w-full text-left">
          <p className="muted mb-2 text-xs">
            From backend/ with the virtual environment activated:
          </p>
          <code className="break-safe block rounded bg-[var(--subtle)] p-3 text-xs">
            python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
          </code>
        </div>
      )}
      <div className="flex flex-wrap justify-center gap-3">
        <RefreshButton />
        <Link className="button" href="/repositories" prefetch={false}>
          Repositories
        </Link>
      </div>
    </section>
  );
}
