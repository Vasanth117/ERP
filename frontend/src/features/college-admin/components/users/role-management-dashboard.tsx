"use client";

import Link from "next/link";
import { useState } from "react";

import { ArrowLeftRightIcon } from "@/components/icons/erp/generated/arrow-left-right";
import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { CollegeAdminKpiGrid, CollegeAdminUserDashboardKpiCard } from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useRoleManagementDashboardPage } from "@/features/college-admin/hooks/use-role-management-dashboard";
import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    error: "bg-[#ef4444]",
    muted: "bg-[#9ca3af]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}


export function RoleManagementDashboard() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useRoleManagementDashboardPage(page);

  return (
    <div className="space-y-5" data-figma-frame="69:126349">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Role Management Dashboard"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            href={data?.compare_roles_href ?? "/college-admin/users/permission-management"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            <ArrowLeftRightIcon className="size-3.5" aria-hidden />
            {data?.compare_roles_label ?? "Compare roles"}
          </Link>
          <Link
            href={data?.create_role_href ?? "/college-admin/users/create-edit-role"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <PlusIcon className="size-3.5" aria-hidden />
            {data?.create_role_label ?? "Create role"}
          </Link>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <CollegeAdminKpiGrid>
              {data.kpis.map((kpi, index) => (
                <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
              ))}
            </CollegeAdminKpiGrid>

            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.roles_section_title}</h3>
                <span className="text-[12px] text-[#6b7280]">{data.roles_count_label}</span>
              </div>
              {data.roles.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[52rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.table_headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn("pb-3 font-medium", index === 0 ? "px-5" : "pr-3")}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.roles.map((row) => (
                        <tr key={row.role_id} className="hover:bg-[#f9fafb]">
                          <td className="px-5 py-3 font-medium text-[#111827]">
                            <Link href={row.detail_href} className="hover:text-[#245dd8]">
                              {row.role_name}
                            </Link>
                          </td>
                          <td className="py-3 pr-3 text-[#374151]">{row.type_label}</td>
                          <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.users_count}</td>
                          <td className="py-3 pr-3 text-[#374151]">{row.modules_label}</td>
                          <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.last_changed_label}</td>
                          <td className="py-3 pr-5">
                            <StatusPill label={row.status_label} tone={row.status_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">
                  No institution roles yet.{" "}
                  <Link href={data.create_role_href} className="font-medium text-[#245dd8] hover:underline">
                    Create a role
                  </Link>{" "}
                  to get started.
                </p>
              )}
              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                <span>{data.showing_label}</span>
                {data.pagination.total_pages > 0 ? (
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
                      disabled={!data.pagination.has_previous}
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                    >
                      ‹
                    </button>
                    {data.pagination.page_numbers.map((num, index) =>
                      num === -1 ? (
                        <span key={`ellipsis-${index}`} className="px-1">
                          …
                        </span>
                      ) : (
                        <button
                          key={num}
                          type="button"
                          className={cn(
                            "min-w-8 rounded border px-2 py-1 tabular-nums",
                            num === data.pagination.page
                              ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]"
                              : "border-[#dce3ec]",
                          )}
                          onClick={() => setPage(num)}
                        >
                          {num}
                        </button>
                      ),
                    )}
                    <button
                      type="button"
                      className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
                      disabled={!data.pagination.has_next}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      ›
                    </button>
                  </div>
                ) : null}
              </div>
            </section>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}