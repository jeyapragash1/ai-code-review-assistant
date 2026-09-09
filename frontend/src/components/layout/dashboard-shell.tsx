"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useRef, useState } from "react";
import { useTheme } from "next-themes";
import {
  Bell,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  CodeXml,
  ExternalLink,
  FolderGit2,
  GitPullRequest,
  LayoutDashboard,
  Menu,
  Moon,
  Search,
  Settings,
  ShieldCheck,
  Sun,
  X,
} from "lucide-react";
import { navigation } from "@/lib/navigation";
import { PRODUCT_NAME, PRODUCT_SUBTITLE, PROJECT_URL } from "@/lib/constants";
import { pullRequests, repositories } from "@/lib/mock-data";
import { Badge, Button, Input } from "@/components/ui";
const icons = {
  dashboard: LayoutDashboard,
  repositories: FolderGit2,
  pullRequests: GitPullRequest,
  reviews: ShieldCheck,
  settings: Settings,
};
export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  return (
    <Button
      className="icon-button"
      aria-label="Toggle color theme"
      title="Toggle color theme"
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
    >
      <Sun size={17} className="hidden dark:block" />
      <Moon size={17} className="dark:hidden" />
    </Button>
  );
}
export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [query, setQuery] = useState("");
  const drawer = useRef<HTMLDialogElement>(null);
  const search = useRef<HTMLDialogElement>(null);
  const notifications = useRef<HTMLDialogElement>(null);
  const current = navigation.find((n) => pathname.startsWith(n.href));
  const searchItems = [
    ...repositories.map((r) => ({
      title: `${r.owner}/${r.name}`,
      href: `/repositories/${r.id}`,
    })),
    ...pullRequests.map((p) => ({
      title: `#${p.number} ${p.title}`,
      href: `/pull-requests/${p.id}`,
    })),
  ].filter((item) => item.title.toLowerCase().includes(query.toLowerCase()));
  const renderNav = (mobile = false) => (
    <nav
      aria-label={mobile ? "Mobile navigation" : "Main navigation"}
      className="flex flex-col gap-1"
    >
      {navigation.map((n) => {
        const Icon = icons[n.icon];
        const active = pathname.startsWith(n.href);
        return (
          <Link
            key={n.href}
            href={n.href}
            aria-current={active ? "page" : undefined}
            title={n.label}
            onClick={() => drawer.current?.close()}
            className={`flex min-h-11 items-center gap-3 rounded-md px-3 text-[13px] font-medium ${active ? "bg-[var(--accent-soft)] accent" : "muted hover:bg-[var(--subtle)]"}`}
          >
            <Icon size={18} />
            <span
              className={
                mobile ? "" : collapsed ? "hidden" : "hidden xl:inline"
              }
            >
              {n.label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
  return (
    <div className="min-h-screen">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside
        className={`fixed inset-y-0 left-0 z-30 hidden flex-col border-r border-[var(--border)] bg-[var(--surface)] p-4 md:flex ${collapsed ? "w-[76px]" : "w-[76px] xl:w-[236px]"}`}
      >
        <Link
          href="/dashboard"
          aria-label="CodeReview AI dashboard"
          className="mb-9 flex h-10 items-center gap-3 px-2"
        >
          <span className="rounded-md bg-[#3668de] p-1.5 text-white">
            <CodeXml size={21} />
          </span>
          <span
            className={`text-base font-semibold ${collapsed ? "hidden" : "hidden xl:inline"}`}
          >
            {PRODUCT_NAME}
          </span>
        </Link>
        <p
          className={`muted mb-3 px-3 text-[10px] font-semibold ${collapsed ? "hidden" : "hidden xl:block"}`}
        >
          WORKSPACE
        </p>
        {renderNav()}
        <div className="mt-auto flex flex-col gap-4">
          <div
            className={`bordered rounded-md p-3 ${collapsed ? "hidden" : "hidden xl:block"}`}
          >
            <div className="mb-2 flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--green)]" />
              <span className="text-xs font-medium">Demo workspace</span>
            </div>
            <p className="muted text-[11px] leading-relaxed">
              A snapshot of your code review workflow.
            </p>
          </div>
          <a
            href={PROJECT_URL}
            target="_blank"
            rel="noreferrer"
            title="Project on GitHub"
            className="muted flex items-center gap-3 px-3 text-xs"
          >
            <BookOpen size={17} />
            <span className={collapsed ? "hidden" : "hidden xl:inline"}>
              View on GitHub
            </span>
            <ExternalLink
              size={12}
              className={collapsed ? "hidden" : "hidden xl:inline"}
            />
          </a>
          <Button
            className="icon-button hidden xl:flex"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </Button>
        </div>
      </aside>
      <div
        className={`min-w-0 md:ml-[76px] ${collapsed ? "" : "xl:ml-[236px]"}`}
      >
        <header className="surface flex h-[68px] items-center justify-between gap-2 border-b border-[var(--border)] px-4 sm:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <Button
              className="icon-button md:hidden"
              aria-label="Open navigation"
              onClick={() => drawer.current?.showModal()}
            >
              <Menu size={18} />
            </Button>
            <span className="muted hidden text-xs sm:inline">Workspace</span>
            <ChevronRight size={13} className="muted hidden sm:block" />
            <span className="truncate text-xs font-medium">
              {current?.label ?? "Workspace"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              className="icon-button"
              aria-label="Search workspace"
              title="Search workspace"
              onClick={() => search.current?.showModal()}
            >
              <Search size={15} />
            </Button>
            <span className="hidden min-[400px]:inline">
              <Badge>Demo data</Badge>
            </span>
            <Button
              className="icon-button"
              aria-label="Notifications"
              title="Notifications"
              onClick={() => notifications.current?.showModal()}
            >
              <Bell size={16} />
            </Button>
            <ThemeToggle />
            <span
              title="Developer profile placeholder"
              aria-label="Developer profile placeholder"
              className="subtle hidden h-8 w-8 items-center justify-center rounded-full border border-[var(--border)] text-[10px] font-semibold sm:flex"
            >
              DV
            </span>
          </div>
        </header>
        <main
          id="main-content"
          className="mx-auto max-w-[1600px] min-w-0 p-4 sm:p-8"
          tabIndex={-1}
        >
          {children}
        </main>
        <footer className="muted flex flex-wrap justify-between gap-2 px-4 pb-6 text-[10px] sm:px-8">
          <span>
            {PRODUCT_NAME} / {PRODUCT_SUBTITLE}
          </span>
          <span>Demo data · Backend integration pending</span>
        </footer>
      </div>
      <dialog ref={drawer} className="w-72" aria-label="Navigation">
        <div className="mb-5 flex items-center justify-between">
          <strong>{PRODUCT_NAME}</strong>
          <Button
            className="icon-button"
            aria-label="Close navigation"
            onClick={() => drawer.current?.close()}
          >
            <X size={17} />
          </Button>
        </div>
        {renderNav(true)}
        <a
          className="accent mt-5 block text-xs"
          href={PROJECT_URL}
          target="_blank"
          rel="noreferrer"
        >
          Project on GitHub
        </a>
      </dialog>
      <dialog ref={search} className="w-[540px]" aria-label="Search workspace">
        <div className="mb-4 flex justify-between">
          <h2 className="font-semibold">Search workspace</h2>
          <Button
            className="icon-button"
            aria-label="Close search"
            onClick={() => search.current?.close()}
          >
            <X size={16} />
          </Button>
        </div>
        <Input
          label="Search repositories and pull requests"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Repository or pull request title"
        />
        <div className="mt-4 max-h-80 overflow-y-auto">
          {searchItems.map((item) => (
            <Link
              className="row row-link block text-sm"
              href={item.href}
              key={item.href}
              onClick={() => search.current?.close()}
            >
              {item.title}
            </Link>
          ))}
          {searchItems.length === 0 && (
            <p className="muted py-5">No matching records.</p>
          )}
        </div>
      </dialog>
      <dialog ref={notifications} className="w-96" aria-label="Notifications">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Notifications</h2>
          <Button
            className="icon-button"
            aria-label="Close notifications"
            onClick={() => notifications.current?.close()}
          >
            <X size={16} />
          </Button>
        </div>
        <p className="muted mt-5 text-sm">
          No live notifications. This workspace uses demo data.
        </p>
      </dialog>
    </div>
  );
}
