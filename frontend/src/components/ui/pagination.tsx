import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { Page } from "@/types/api";
import type { Query } from "@/lib/api/client";
import { pageHref } from "@/lib/api/filters";
export function Pagination({
  data,
  path,
  query,
}: {
  data: Omit<Page<unknown>, "items">;
  path: string;
  query: Query;
}) {
  const previous = data.page > 1,
    next = data.page < data.total_pages;
  return (
    <nav
      aria-label="Pagination"
      className="flex flex-wrap items-center justify-between gap-4 py-3"
    >
      <p className="muted text-xs">
        {data.total} results ·{" "}
        {data.total_pages === 0
          ? "No pages"
          : `Page ${data.page} of ${data.total_pages}`}
      </p>
      <div className="flex gap-2">
        {previous ? (
          <Link
            className="button"
            prefetch={false}
            href={pageHref(path, query, data.page - 1)}
          >
            <ChevronLeft size={14} />
            Previous
          </Link>
        ) : (
          <button className="button" disabled>
            <ChevronLeft size={14} />
            Previous
          </button>
        )}
        {next ? (
          <Link
            className="button"
            prefetch={false}
            href={pageHref(path, query, data.page + 1)}
          >
            Next
            <ChevronRight size={14} />
          </Link>
        ) : (
          <button className="button" disabled>
            Next
            <ChevronRight size={14} />
          </button>
        )}
      </div>
    </nav>
  );
}
