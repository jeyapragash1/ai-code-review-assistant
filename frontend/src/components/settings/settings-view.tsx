"use client";
import { useState, useSyncExternalStore } from "react";
import { useTheme } from "next-themes";
import {
  Bell,
  GitFork as Github,
  LockKeyhole,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react";
import { Badge, PageHeading, Select } from "@/components/ui";
const subscribe = () => () => {};
export function SettingsView() {
  const [threshold, setThreshold] = useState("low");
  const [ai, setAi] = useState(true);
  const [staticAnalysis, setStaticAnalysis] = useState(true);
  const [highAlerts, setHighAlerts] = useState(true);
  const [completeAlerts, setCompleteAlerts] = useState(false);
  const [density, setDensity] = useState("comfortable");
  const { theme, setTheme } = useTheme();
  const mounted = useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
  return (
    <div className="page-stack max-w-4xl">
      <PageHeading
        title="Settings"
        description="Workspace preferences, review defaults, and privacy."
      />
      <p className="bordered rounded-md px-4 py-3 text-xs muted" role="status">
        Demo preferences apply to this preview only. Backend persistence will be
        connected later. Theme is saved in this browser.
      </p>
      <section className="border-b border-[var(--border)] pb-6">
        <h2 className="section-title mb-4 flex items-center gap-2">
          <SlidersHorizontal size={16} className="accent" />
          General preferences
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Select
            label="Preferred review detail (demo)"
            value={density}
            onChange={(e) => setDensity(e.target.value)}
          >
            <option value="comfortable">Detailed explanations</option>
            <option value="compact">Concise summaries</option>
          </Select>
          <Select
            label="Review severity threshold (demo)"
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
          >
            <option value="low">Low and above</option>
            <option value="medium">Medium and above</option>
            <option value="high">High only</option>
          </Select>
        </div>
      </section>
      <section className="border-b border-[var(--border)] pb-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="section-title flex items-center gap-2">
            <Github size={17} />
            GitHub integration
          </h2>
          <Badge>Not connected</Badge>
        </div>
        <p className="muted mt-3 text-sm">
          Repository connections and webhook configuration are not available in
          this demo.
        </p>
      </section>
      <section className="space-y-4 border-b border-[var(--border)] pb-6">
        <h2 className="section-title flex items-center gap-2">
          <Sparkles size={16} className="accent" />
          AI review configuration
        </h2>
        <Toggle
          label="Contextual AI analysis"
          description="Proposed preference for contextual security and quality checks."
          checked={ai}
          onChange={setAi}
        />
        <Toggle
          label="Static analysis"
          description="Proposed preference for deterministic rules and pattern checks."
          checked={staticAnalysis}
          onChange={setStaticAnalysis}
        />
        <p className="muted text-xs">
          No AI service is connected. No source code leaves this demo.
        </p>
      </section>
      <section className="space-y-4 border-b border-[var(--border)] pb-6">
        <h2 className="section-title flex items-center gap-2">
          <Bell size={16} className="accent" />
          Notification preferences
        </h2>
        <Toggle
          label="High-severity findings"
          description="Notify when a review identifies a high-severity issue."
          checked={highAlerts}
          onChange={setHighAlerts}
        />
        <Toggle
          label="Review completed"
          description="Notify when pull request analysis is ready."
          checked={completeAlerts}
          onChange={setCompleteAlerts}
        />
      </section>
      <section className="border-b border-[var(--border)] pb-6">
        <h2 className="section-title mb-4">Appearance</h2>
        <div className="max-w-sm">
          <Select
            label="Theme preference"
            value={mounted ? theme : "dark"}
            onChange={(e) => setTheme(e.target.value)}
          >
            <option value="dark">Dark</option>
            <option value="light">Light</option>
            <option value="system">System</option>
          </Select>
        </div>
      </section>
      <section>
        <h2 className="section-title flex items-center gap-2">
          <LockKeyhole size={16} className="accent" />
          Data and privacy
        </h2>
        <p className="muted mt-3 text-sm leading-7">
          This workspace uses fictional repositories and escaped sample code. It
          does not request backend data, access your GitHub account, or transmit
          feedback. Never paste tokens, webhook secrets, or private source code
          into demo fields.
        </p>
      </section>
    </div>
  );
}
function Toggle({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between gap-5">
      <span>
        <span className="block text-sm font-medium">{label}</span>
        <span className="muted mt-1 block text-xs">{description}</span>
      </span>
      <input
        type="checkbox"
        role="switch"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="h-4 w-4 shrink-0 accent-[#3668de]"
      />
    </label>
  );
}
