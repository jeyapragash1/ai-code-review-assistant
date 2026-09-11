import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/api/auth";
import { backendCookie, load } from "@/lib/api/server";
export default async function Home() {
  const result = await load(async () => getCurrentUser(await backendCookie()));
  redirect(result.ok ? "/dashboard" : "/login");
}
