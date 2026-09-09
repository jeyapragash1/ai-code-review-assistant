import { ExternalLink } from "lucide-react";
export function GitHubLink({ query }: { query: string }) {
  return (
    <a
      className="button"
      href={`https://github.com/search?q=${encodeURIComponent(query)}&type=repositories`}
      target="_blank"
      rel="noreferrer"
    >
      <ExternalLink size={14} />
      GitHub search <span className="muted text-[10px]">Demo</span>
    </a>
  );
}
