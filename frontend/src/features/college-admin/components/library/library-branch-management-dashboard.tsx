"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import Link from "next/link";

import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useLibraryBranchManagementPage } from "@/features/college-admin/hooks/use-library-branch-management";
import type { LibraryBranchManagementPage } from "@/features/college-admin/types/library-branch-management";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    error: "bg-[#ef4444]",
    info: "bg-[#3b82f6]",
    muted: "bg-[#9ca3af]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium",
        styles[key],
      )}
    >
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}

function mergeView(data: LibraryBranchManagementPage | undefined) {
  return {
    page_title: data?.page_title ?? "",
    page_subtitle: data?.page_subtitle ?? "",
    add_branch_label: data?.add_branch_label ?? "",
    add_branch_href: data?.add_branch_href ?? "#",
    branches_section_title: data?.branches_section_title ?? "",
    branches_count_label: data?.branches_count_label ?? "",
    table_headers: data?.table_headers ?? [],
    branch_rows: data?.branch_rows ?? [],
    empty_table_message: data?.empty_table_message ?? "",
  };
}

export function LibraryBranchManagementDashboard() {
  const { data, isLoading, isError, error, refetch, isFetching } = useLibraryBranchManagementPage();
  const view = mergeView(data);

  return (
    <CollegeAdminModulePageLayout figmaFrame="160:11930">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {view.page_title || "Library Branch Management"}
          </h2>
          {view.page_subtitle ? (
            <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p>
          ) : null}
        </div>
        <Link
          href={view.add_branch_href}
          className="inline-flex h-9 shrink-0 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
        >
          <CollegeAdminPlusActionLabel label={view.add_branch_label || "Add branch"} />
        </Link>
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading branches…" : "Updating…"}</p>
      ) : null}

      {isError ? (
        <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
          <></>
        </QueryState>
      ) : !data ? null : (
        <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
          <div className="border-b border-[#f1f5f9] px-5 py-3.5">
            <h3 className="text-[14px] font-semibold text-[#111827]">
              {view.branches_section_title || "Branches"}
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[48rem] text-left text-[13px]">
              <thead>
                <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                  {view.table_headers.map((header, index, headers) => (
                    <th
                      key={header}
                      className={cn(
                        "pb-3 pt-4 font-medium",
                        index === 0 ? "pl-5 pr-3" : "pr-3",
                        index === headers.length - 1 ? "pr-5 text-right" : "",
                        index >= 2 && index <= 3 ? "text-right tabular-nums" : "",
                      )}
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f1f5f9]">
                {view.branch_rows.length ? (
                  view.branch_rows.map((row) => (
                    <tr key={row.branch_code} className="text-[#374151] hover:bg-[#f9fafb]">
                      <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                        <Link href={row.detail_href} className="hover:text-[#245dd8]">
                          {row.branch_name}
                        </Link>
                      </td>
                      <td className="py-3 pr-3 text-[#6b7280]">{row.location_label}</td>
                      <td className="py-3 pr-3 text-right tabular-nums">{row.titles_label}</td>
                      <td className="py-3 pr-3 text-right tabular-nums">{row.seats_label}</td>
                      <td className="py-3 pr-3 text-[#6b7280]">{row.hours_label}</td>
                      <td className="py-3 pr-5 text-right">
                        <StatusPill label={row.status_label} tone={row.status_tone} />
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td
                      colSpan={Math.max(view.table_headers.length, 1)}
                      className="px-5 py-10 text-center text-sm text-[#9ca3af]"
                    >
                      {view.empty_table_message}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
            {view.branches_count_label}
          </div>
        </section>
      )}
    </CollegeAdminModulePageLayout>
  );
}