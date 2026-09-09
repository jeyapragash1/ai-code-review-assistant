import { Skeleton } from "@/components/ui";
export default function Loading() {
  return (
    <div role="status" className="page-stack p-5">
      <span className="muted text-sm">Loading workspace...</span>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} />
        ))}
      </div>
      <Skeleton />
      <Skeleton />
    </div>
  );
}
