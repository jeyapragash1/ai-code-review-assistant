"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
export function JobButton({ endpoint, label, disabled = false }: { endpoint: string; label: string; disabled?: boolean }) {
  const router = useRouter();
  const [state, setState] = useState<"idle" | "loading" | "success" | "failed">("idle");
  async function submit() {
    setState("loading");
    try {
      const response = await fetch(endpoint, { method: "POST", credentials: "same-origin" });
      setState(response.ok ? "success" : "failed");
      router.refresh();
    } catch { setState("failed"); }
  }
  return <div><button className="button" type="button" disabled={disabled || state === "loading"} onClick={submit}>{state === "loading" ? "Please wait…" : label}</button><p role="status" aria-live="polite" className="muted mt-2 text-sm">{state === "success" ? "Request accepted. Refresh to see the latest status." : state === "failed" ? "Request failed. Check service configuration and access, then try again." : ""}</p></div>;
}
