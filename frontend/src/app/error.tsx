"use client";
export default function ErrorPage({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div role="alert" className="mx-auto max-w-lg space-y-4 p-8">
      <h1 className="text-xl font-semibold">Unable to display this page</h1>
      <p className="muted">Please try again or return to the dashboard.</p>
      <button className="button primary" onClick={reset}>
        Try again
      </button>
      <a href="/dashboard" className="button ml-3">
        Dashboard
      </a>
    </div>
  );
}
