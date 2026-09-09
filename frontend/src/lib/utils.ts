export function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(value));
}
export function label(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
export function shortSha(value: string) {
  return value.slice(0, 7);
}
