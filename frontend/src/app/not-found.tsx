import Link from "next/link";
import { SearchX } from "lucide-react";
export default function NotFound() {
  return (
    <section aria-label="Record not found" className="mx-auto flex min-h-[65vh] max-w-lg flex-col items-center justify-center gap-5 p-6 text-center">
      <SearchX size={36} className="muted" />
      <p className="muted text-xs">404 / RECORD NOT FOUND</p>
      <h1 className="text-2xl font-semibold">
        This record is not in the workspace
      </h1>
      <p className="muted">
        The link may be incorrect, or the record is not available. Review
        records are not implemented yet.
      </p>
      <Link href="/dashboard" className="button primary">
        Back to dashboard
      </Link>
      <Link href="/reviews" className="button" prefetch={false}>
        Back to reviews
      </Link>
    </section>
  );
}
