"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";

import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useDepartmentResourceManagementPage } from "@/features/college-admin/hooks/use-department-resource-management";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    info: "bg-[#3b82f6]",
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

function formatSnapshot(iso: string) {
  try {
    return new Intl.DateTimeFormat("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Asia/Kolkata",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function DepartmentResourceManagementDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const departmentId = searchParams.get("departmentId") ?? undefined;
  const view = searchParams.get("view") ?? undefined;

  const { data, isLoading, isError, error, refetch, isFetching } = useDepartmentResourceManagementPage(departmentId, view);

  const selectDepartment = useCallback(
    (id: string) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set("departmentId", id);
      params.delete("view");
      router.push(`/college-admin/organization/department-resource-management?${params.toString()}`);
    },
    [router, searchParams],
  );

  const headers = data?.laboratories_table_headers ?? [];

  const subtitleToneClass = useMemo(
    () => ({
      success: "text-[#047857]",
      warning: "text-[#c2410c]",
      muted: "text-[#6b7280]",
    }),
    [],
  );

  return (
    <div className="space-y-5" data-figma-frame="69:134809">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Department Resource Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
        {data ? (
          <Link
            href={data.request_resource_href}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <PlusIcon className="size-3.5" aria-hidden />
            {data.request_resource_label}
          </Link>
        ) : null}
      </div>

      {data ? (
        <div className="flex flex-col gap-3 border-b border-[#e8ecf2] pb-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-1">
              {data.department_tabs.map((tab) => {
                const active = tab.department_id === data.selected_department_id;
                return (
                  <button
                    key={tab.department_id}
                    type="button"
                    onClick={() => selectDepartment(tab.department_id)}
                    className={cn(
                      "rounded-md border px-3 py-1.5 text-[13px] font-medium transition-colors",
                      active
                        ? "border-[#dce3ec] bg-white text-[#111827] shadow-sm"
                        : "border-transparent text-[#6b7280] hover:bg-[#f9fafb]",
                    )}
                  >
                    {tab.label}
                  </button>
                );
              })}
              {data.more_department_options.length ? (
                <select
                  aria-label={data.more_departments_label}
                  className="h-8 rounded-md border border-[#dce3ec] bg-white px-2 text-[13px] text-[#374151]"
                  value=""
                  onChange={(e) => {
                    if (e.target.value) selectDepartment(e.target.value);
                  }}
                >
                  <option value="">{data.more_departments_label}</option>
                  {data.more_department_options.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              ) : null}
            </div>
            <div className="flex items-center gap-3">
              <Link
                href={data.faculty_nav_href}
                className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-4 text-[13px] font-medium text-[#245dd8] hover:bg-[#eff6ff]"
              >
                {data.faculty_nav_label}
              </Link>
              <span className="text-[12px] tabular-nums text-[#9ca3af]">{data.updated_at_label}</span>
            </div>
          </div>
        </div>
      ) : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()} isEmpty={false}>
        {data ? (
          <div className={cn("space-y-5", isFetching && "opacity-70")}>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {data.kpi_cards.map((card) => (
                <article
                  key={card.key}
                  className="rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)]"
                >
                  <p className="text-[12px] font-medium text-[#6b7280]">{card.title}</p>
                  <p className="mt-1 text-[28px] font-bold tabular-nums tracking-tight text-[#111827]">{card.value}</p>
                  <p
                    className={cn(
                      "mt-1 text-[12px]",
                      subtitleToneClass[card.subtitle_tone as keyof typeof subtitleToneClass] ?? "text-[#6b7280]",
                    )}
                  >
                    {card.subtitle}
                  </p>
                </article>
              ))}
            </div>

            <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_18rem]">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.laboratories_section_title}</h3>
                </div>
                {data.laboratory_rows.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[36rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {headers.map((h, i) => (
                            <th key={h} className={cn("pb-3 pt-4 font-medium", i === 0 ? "px-5" : "pr-3")}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.laboratory_rows.map((row) => (
                          <tr key={row.lab_id} className="hover:bg-[#f9fafb]">
                            <td className="px-5 py-3 font-medium text-[#111827]">{row.lab_name}</td>
                            <td className="py-3 pr-3 text-[#374151]">{row.room_label}</td>
                            <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.capacity}</td>
                            <td className="py-3 pr-3 text-[#374151]">{row.systems_label}</td>
                            <td className="py-3 pr-5">
                              <StatusPill label={row.status_label} tone={row.status_tone} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-8 text-sm text-[#9ca3af]">No laboratories linked to this department yet.</p>
                )}
                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  <span>{data.laboratories_footer_count_label}</span>
                  {data.laboratories_view_all_href ? (
                    <Link href={data.laboratories_view_all_href} className="font-medium text-[#245dd8] hover:underline">
                      {data.laboratories_view_all_label} →
                    </Link>
                  ) : null}
                </div>
              </section>

              <aside className="space-y-4">
                <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.budget_section_title}</h3>
                  <ul className="mt-4 space-y-4">
                    {data.budget_bars.map((bar) => (
                      <li key={bar.key}>
                        <div className="flex items-center justify-between text-[12px] text-[#6b7280]">
                          <span>{bar.label}</span>
                          <span className="tabular-nums text-[#111827]">
                            {bar.spent_label} of {bar.cap_label}
                          </span>
                        </div>
                        <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-[#e5e7eb]">
                          <div
                            className="h-full rounded-full bg-[#245dd8]"
                            style={{
                              width: `${bar.cap_amount ? Math.min(100, (bar.spent_amount / bar.cap_amount) * 100) : 0}%`,
                            }}
                          />
                        </div>
                      </li>
                    ))}
                  </ul>
                </section>

                <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.open_requests_section_title}</h3>
                  <ul className="mt-3 space-y-3">
                    {data.open_requests.length ? (
                      data.open_requests.map((req) => (
                        <li key={req.request_id} className="border-b border-[#f1f5f9] pb-3 last:border-0 last:pb-0">
                          <p className="text-[13px] font-medium text-[#111827]">{req.title}</p>
                          <div className="mt-1 flex items-center justify-between gap-2">
                            <p className="text-[12px] text-[#6b7280]">{req.detail_line}</p>
                            <StatusPill label={req.status_tag} tone={req.status_tone} />
                          </div>
                        </li>
                      ))
                    ) : (
                      <li className="text-[13px] text-[#9ca3af]">No open resource requests.</li>
                    )}
                  </ul>
                </section>
              </aside>
            </div>

            <footer className="flex flex-col gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
              <p>{data.footer_disclaimer}</p>
              <p className="tabular-nums">
                {data.footer_snapshot_label} · {formatSnapshot(data.generated_at)}
              </p>
            </footer>
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}