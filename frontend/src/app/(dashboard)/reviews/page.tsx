import Link from "next/link";
import { Card, EmptyState, PageHeading } from "@/components/ui";
export default function Page() {
  return (
    <div className="page-stack">
      <PageHeading
        title="Reviews"
        description="AI-assisted code review results."
      />
      <Card>
        <EmptyState
          title="No AI reviews are available yet."
          description="The review engine has not been connected."
        >
          <p className="muted max-w-md text-sm leading-7">
            In a later phase, synchronized Pull Requests will be analyzed and
            their results will appear here for human verification.
          </p>
          <Link href="/pull-requests" className="button" prefetch={false}>
            View Pull Requests
          </Link>
        </EmptyState>
      </Card>
    </div>
  );
}
