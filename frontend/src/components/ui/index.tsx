import Link from "next/link";
import { ChevronRight, SearchX, ShieldCheck } from "lucide-react";
import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
} from "react";
import type { ReviewFinding } from "@/types";
import { label } from "@/lib/utils";
import { SEVERITIES } from "@/lib/constants";
export function Button({
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button className={`button ${className}`} {...props} />;
}
export function Badge({
  children,
  tone = "",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
export function StatusBadge({ status }: { status: string }) {
  return (
    <Badge tone={status}>
      <span aria-hidden="true">&#9679;</span>
      {label(status)}
    </Badge>
  );
}
export function SeverityBadge({ severity }: { severity: string }) {
  return (
    <Badge tone={severity}>
      {severity === "clear"
        ? "No findings"
        : severity === "pending"
          ? "Not assessed"
          : `${label(severity)} risk`}
    </Badge>
  );
}
export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`panel ${className}`}>{children}</div>;
}
export function PageHeading({
  title,
  description,
  action,
  eyebrow,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  eyebrow?: string;
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="min-w-0">
        {eyebrow && <p className="muted mb-2 text-xs">{eyebrow}</p>}
        <h1 className="break-safe text-2xl font-semibold">{title}</h1>
        {description && (
          <p className="muted mt-2 max-w-2xl text-sm">{description}</p>
        )}
      </div>
      {action}
    </div>
  );
}
export function Input({
  label: fieldLabel,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className="flex min-w-0 flex-col gap-1.5">
      <span className="text-xs muted">{fieldLabel}</span>
      <input className="field" {...props} />
    </label>
  );
}
export function Select({
  label: fieldLabel,
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & { label: string }) {
  return (
    <label className="flex min-w-0 flex-col gap-1.5">
      <span className="text-xs muted">{fieldLabel}</span>
      <select className="field" {...props}>
        {children}
      </select>
    </label>
  );
}
export function EmptyState({
  title = "No results found",
  description = "Try a different search or clear your filters.",
  children,
}: {
  title?: string;
  description?: string;
  children?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-3 px-5 py-14 text-center">
      <SearchX size={28} className="muted" />
      <h2 className="font-semibold">{title}</h2>
      <p className="muted text-sm">{description}</p>
      {children}
    </div>
  );
}
export function StatCard({
  label: title,
  value,
  detail,
  icon,
  tone,
}: {
  label: string;
  value: string | number;
  detail: string;
  icon: ReactNode;
  tone?: string;
}) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between gap-2">
        <p className="muted text-xs">{title}</p>
        <span className={tone || "muted"}>{icon}</span>
      </div>
      <p className="my-3 text-3xl font-semibold tabular-nums">{value}</p>
      <p className="muted text-xs">{detail}</p>
    </Card>
  );
}
export function Breadcrumbs({
  items,
}: {
  items: { label: string; href?: string }[];
}) {
  return (
    <nav
      aria-label="Breadcrumb"
      className="flex flex-wrap items-center gap-2 text-xs muted"
    >
      {items.map((item, i) => (
        <span className="flex items-center gap-2 break-safe" key={item.label}>
          {i > 0 && <ChevronRight size={12} />}{" "}
          {item.href ? (
            <Link href={item.href} className="hover:underline">
              {item.label}
            </Link>
          ) : (
            <span aria-current="page">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
export function RiskSummary({ findings }: { findings: ReviewFinding[] }) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {SEVERITIES.map((s) => (
        <Badge key={s} tone={s}>
          {findings.filter((f) => f.severity === s).length} {label(s)}
        </Badge>
      ))}
      {findings.length === 0 && (
        <ShieldCheck size={17} className="text-[var(--green)]" />
      )}
    </div>
  );
}
export function Skeleton() {
  return <div className="skeleton" aria-hidden="true" />;
}
export function Table({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="data-table">{children}</table>
    </div>
  );
}
