import Link from "next/link";
import { Button, Input, Select } from "./index";
import type { Repository } from "@/types/repository";
import type { Query } from "@/lib/api/client";
export function Filters({
  path,
  values,
  mode,
  repositories = [],
}: {
  path: string;
  values: Query;
  mode: "repositories" | "pull-requests" | "nested";
  repositories?: Repository[];
}) {
  return (
    <form method="get" action={path} className="flex flex-wrap items-end gap-3">
      <input type="hidden" name="page" value="1" />
      {mode !== "nested" && (
        <div className="min-w-0 flex-[2_1_220px]">
          <Input
            label="Search"
            name="search"
            maxLength={200}
            defaultValue={String(values.search ?? "")}
            placeholder={
              mode === "repositories"
                ? "Owner or repository name"
                : "Pull request title or author"
            }
          />
        </div>
      )}
      {mode === "repositories" ? (
        <Select
          label="Active state"
          name="is_active"
          defaultValue={String(values.is_active ?? "")}
        >
          <option value="">All repositories</option>
          <option value="true">Active</option>
          <option value="false">Inactive</option>
        </Select>
      ) : (
        <>
          <Select
            label="Status"
            name="status"
            defaultValue={String(values.status ?? "")}
          >
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="closed">Closed</option>
            <option value="merged">Merged</option>
          </Select>
          {mode === "pull-requests" && (
            <div className="min-w-0 max-w-full sm:max-w-xs">
              <Select
                label="Repository"
                name="repository_id"
                defaultValue={String(values.repository_id ?? "")}
              >
                <option value="">All repositories</option>
                {repositories.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.full_name}
                  </option>
                ))}
              </Select>
            </div>
          )}
        </>
      )}
      <div className="w-24">
        <Input
          label="Page size"
          name="page_size"
          type="number"
          min={1}
          max={100}
          required
          defaultValue={String(values.page_size ?? 20)}
        />
      </div>
      <Button type="submit" className="primary">
        Apply
      </Button>
      <Link className="button" href={path} prefetch={false}>
        Clear
      </Link>
    </form>
  );
}
