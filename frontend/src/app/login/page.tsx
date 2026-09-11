import { redirect } from "next/navigation";
import { CodeXml, LockKeyhole } from "lucide-react";
import { getCurrentUser, loginUrl } from "@/lib/api/auth";
import { backendCookie, load } from "@/lib/api/server";
import { Card } from "@/components/ui";

const messages: Record<string, string> = { oauth_failed: "GitHub sign-in could not be completed. Please try again.", access_denied: "This account is not allowed to access this development workspace." };
export default async function Login({ searchParams }: { searchParams: Promise<{ error?: string; next?: string }> }) {
  const query = await searchParams;
  const cookie = await backendCookie();
  const current = await load(() => getCurrentUser(cookie));
  if (current.ok) redirect("/dashboard");
  const nextPath = query.next?.startsWith("/") && !query.next.startsWith("//") && !query.next.includes("\\") && !query.next.includes("%") ? query.next : "/dashboard";
  return <main className="mx-auto flex min-h-screen max-w-lg items-center p-5"><Card className="w-full p-7"><CodeXml className="mb-5 text-[var(--accent)]" size={32}/><p className="muted text-xs">CODE REVIEW AI</p><h1 className="mt-2 text-2xl font-semibold">Sign in with GitHub</h1><p className="muted mt-3 leading-7">Access your synchronized Pull Requests and persisted static-analysis results. Repository installation is a separate later step.</p>{query.error && <p role="alert" className="mt-4 text-sm text-[var(--red)]">{messages[query.error] ?? "Sign-in is temporarily unavailable."}</p>}<a className="button primary mt-6 w-full justify-center" href={loginUrl(nextPath)}><LockKeyhole size={16}/>Continue with GitHub</a><p className="muted mt-5 text-xs leading-6">Authentication uses a secure HTTP-only session cookie. GitHub access tokens are never sent to this browser.</p></Card></main>;
}
