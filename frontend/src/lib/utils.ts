export function formatDate(value: string | null, fallback = "Not available") {
  if (!value || !Number.isFinite(Date.parse(value))) return fallback;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(value));
}
export function formatDateTime(
  value: string | null,
  fallback = "Not available",
) {
  if (!value || !Number.isFinite(Date.parse(value))) return fallback;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(new Date(value));
}
export function formatDuration(ms: number | null) {
  if (ms === null) return "Not available";
  if (ms < 1000) return `${ms} ms`;
  const seconds = ms / 1000;
  return seconds < 60 ? `${seconds.toFixed(1)} s` : `${Math.round(seconds / 60)} min`;
}
export function formatConfidence(value: string) {
  const n = Number(value);
  return Number.isFinite(n) ? `${Math.round(n * 100)}%` : "Not available";
}
export function label(value: string) {
  return value
    .split(/[_-]/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
export function shortSha(value: string) {
  return value.slice(0, 7);
}
