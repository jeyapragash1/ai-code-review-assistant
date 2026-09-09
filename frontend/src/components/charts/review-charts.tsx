"use client";
import { useSyncExternalStore } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ReviewActivityPoint, ReviewFinding } from "@/types";
import { SEVERITIES } from "@/lib/constants";
import { label } from "@/lib/utils";
const subscribe = () => () => {};
const tooltipStyle = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  color: "var(--foreground)",
  fontSize: 12,
};
export function ActivityChart({ data }: { data: ReviewActivityPoint[] }) {
  const mounted = useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
  return (
    <div>
      <div
        className="h-[230px] min-w-0"
        role="img"
        aria-label={`Review activity: ${data.map((p) => `${p.date}: ${p.reviews} completed reviews, ${p.findings} findings`).join("; ")}`}
      >
        {mounted && (
          <ResponsiveContainer width="100%" height="100%" minWidth={0}>
            <AreaChart
              data={data}
              margin={{ top: 15, right: 14, left: -25, bottom: 0 }}
            >
              <CartesianGrid
                vertical={false}
                stroke="var(--border)"
                strokeDasharray="3 4"
              />
              <XAxis
                dataKey="date"
                tick={{ fill: "var(--muted)", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                minTickGap={12}
              />
              <YAxis
                allowDecimals={false}
                tick={{ fill: "var(--muted)", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip contentStyle={tooltipStyle} />
              <Area
                type="linear"
                dataKey="findings"
                name="Findings"
                stroke="#bd91eb"
                fill="#bd91eb"
                fillOpacity={0.06}
                strokeWidth={2}
                isAnimationActive={false}
              />
              <Area
                type="linear"
                dataKey="reviews"
                name="Completed reviews"
                stroke="#7fa3ff"
                fill="#7fa3ff"
                fillOpacity={0.1}
                strokeWidth={2}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
      <div className="muted mt-2 flex flex-wrap justify-center gap-5 text-[11px]">
        <span>
          <span className="text-[#7fa3ff]">●</span> Completed reviews
        </span>
        <span>
          <span className="text-[#bd91eb]">●</span> Findings
        </span>
      </div>
    </div>
  );
}
export function SeverityChart({ findings }: { findings: ReviewFinding[] }) {
  const mounted = useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
  const data = SEVERITIES.map((s) => ({
    name: label(s),
    value: findings.filter((f) => f.severity === s).length,
  }));
  return (
    <div>
      <div
        className="relative h-[200px]"
        role="img"
        aria-label={data.map((d) => `${d.name}: ${d.value}`).join(", ")}
      >
        {mounted && findings.length > 0 && (
          <ResponsiveContainer width="100%" height="100%" minWidth={0}>
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={62}
                outerRadius={82}
                paddingAngle={5}
                stroke="none"
                isAnimationActive={false}
              >
                {["#ef7f8b", "#dfb45d", "#7fa3ff"].map((c) => (
                  <Cell fill={c} key={c} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        )}
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <strong className="text-3xl">{findings.length}</strong>
          <span className="muted text-xs">total findings</span>
        </div>
      </div>
      <div className="flex justify-center gap-5">
        {data.map((d, i) => (
          <div key={d.name} className="text-center">
            <p className={`badge ${SEVERITIES[i]}`}>{d.name}</p>
            <p className="mt-1 text-sm font-semibold">{d.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
