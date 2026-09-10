"use client";
import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { RefreshCw } from "lucide-react";
import { Button } from "./index";
export function RefreshButton() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  return (
    <Button
      disabled={pending}
      onClick={() => startTransition(() => router.refresh())}
      aria-label="Refresh backend data"
    >
      <RefreshCw size={14} />
      {pending ? "Refreshing..." : "Refresh"}
    </Button>
  );
}
