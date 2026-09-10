import { ExternalLink } from "lucide-react";
export function GitHubLink({ url }: { url: string | null }) {
  let safe: URL;
  try {
    safe = new URL(url ?? "");
    if (
      safe.protocol !== "https:" ||
      safe.hostname !== "github.com" ||
      safe.username ||
      safe.password
    )
      return null;
  } catch {
    return null;
  }
  return (
    <a className="button" href={safe.href} target="_blank" rel="noreferrer">
      <ExternalLink size={14} />
      View on GitHub
    </a>
  );
}
