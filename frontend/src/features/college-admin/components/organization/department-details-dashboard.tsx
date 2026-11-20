"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useMemo } from "react";

import { ChartNetworkIcon } from "@/components/icons/erp/generated/chart-network";
import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { MailIcon } from "@/components/icons/erp/generated/mail";
import { NetworkIcon } from "@/components/icons/erp/generated/network";
import { PencilIcon } from "@/components/icons/erp/generated/pencil";
import { PhoneIcon } from "@/components/icons/erp/generated/phone";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useDepartmentDetailsPage } from "@/features/college-admin/hooks/use-department-details";
import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";
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

function ProfileBadge({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    info: "bg-[#3b82f6]",
    warning: "bg-[#f97316]",
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

function KpiCard({ kpi }: { kpi: UserDashboardKpi }) {
  const hintTone =
    kpi.hint_tone === "success"
      ? "text-[#059669]"
      : kpi.hint_tone === "warning"
        ? "text-[#d97706]"
        : "text-[#9ca3af]";
  return (
    <div className="flex min-h-[7rem] flex-col rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <p className="text-[12px] font-medium text-[#6b7280]">{kpi.label}</p>
      <p className="mt-2 text-[26px] font-bold tabular-nums text-[#111827]">{kpi.value}</p>
      <p className={cn("mt-auto pt-2 text-[12px]", hintTone)}>{kpi.hint_line}</p>
    </div>
  );
}

function SectionCard({
  title,
  actionHref,
  actionLabel,
  footer,
  children,
}: {
  title: string;
  actionHref?: string;
  actionLabel?: string;
  footer?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="flex items-center justify-between gap-2 border-b border-[#f1f5f9] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
        {actionHref && actionLabel ? (
          <Link href={actionHref} className="text-[12px] font-medium text-[#245dd8] hover:underline">
            {actionLabel} →
          </Link>
        ) : null}
      </div>
      <div className="px-5 py-1">{children}</div>
      {footer ? (
        <div className="flex items-center justify-between border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
          {footer}
        </div>
      ) : null}
    </section>
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

export function DepartmentDetailsDashboard() {
  const searchParams = useSearchParams();
  const departmentId = useMemo(
    () => searchParams.get("departmentId") ?? searchParams.get("department_id") ?? "",
    [searchParams],
  );
  const { data, isLoading, isError, error, refetch } = useDepartmentDetailsPage(departmentId || null);

  if (!departmentId) {
    return (
      <div className="rounded-xl border border-[#e8ecf2] bg-white p-8 text-center text-sm text-[#6b7280]">
        Select a department from{" "}
        <Link href="/college-admin/organization/all-departments" className="font-medium text-[#245dd8] hover:underline">
          All departments
        </Link>
        .
      </div>
    );
  }

  return (
    <div className="space-y-5" data-figma-frame="69:133413">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex items-start gap-3">
          <Link
            href={data?.back_href ?? "/college-admin/organization/all-departments"}
            className="mt-1 flex size-8 items-center justify-center rounded-md border border-[#dce3ec] text-[#6b7280] hover:bg-[#f9fafb]"
            aria-label={data?.back_label ?? "Back"}
          >
            <ChevronLeftIcon className="size-4" />
          </Link>
          <div>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
              {data?.page_title ?? "Department Details"}
            </h2>
            <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            href={data?.view_report_href ?? "/college-admin/dashboard/department-performance"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            <ChartNetworkIcon className="size-3.5" aria-hidden />
            {data?.view_report_label ?? "View report"}
          </Link>
          <Link
            href={data?.edit_department_href ?? `#`}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <PencilIcon className="size-3.5" aria-hidden />
            {data?.edit_department_label ?? "Edit department"}
          </Link>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
                <div className="flex size-12 shrink-0 items-center justify-center rounded-lg bg-[#eff6ff] text-[#245dd8]">
                  <NetworkIcon className="size-6" aria-hidden />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-[18px] font-bold text-[#111827]">{data.department_name}</h3>
                    {data.profile_badges.map((badge) => (
                      <ProfileBadge key={badge.key} label={badge.label} tone={badge.tone} />
                    ))}
                  </div>
                  <p className="mt-1 text-[13px] text-[#6b7280]">{data.metadata_line}</p>
                  <ul className="mt-3 flex flex-col gap-1 text-[13px] text-[#374151] sm:flex-row sm:flex-wrap sm:gap-x-5">
                    <li>HoD: {data.head_label}</li>
                    <li className="inline-flex items-center gap-1.5">
                      <MailIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                      {data.email_label}
                    </li>
                    <li className="inline-flex items-center gap-1.5">
                      <PhoneIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                      {data.phone_label}
                    </li>
                  </ul>
                </div>
              </div>
            </section>

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {data.kpis.map((kpi) => (
                <KpiCard key={kpi.key} kpi={kpi} />
              ))}
            </div>

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_320px]">
              <div className="space-y-5">
                <SectionCard
                  title={data.programmes_section_title}
                  actionHref={data.programme_mapping_href}
                  actionLabel={data.programme_mapping_label}
                  footer={
                    <>
                      <span>{data.programmes_footer_label}</span>
                      <Link href={data.programmes_view_all_href} className="font-medium text-[#245dd8] hover:underline">
                        View all →
                      </Link>
                    </>
                  }
                >
                  {data.programmes.length ? (
                    <div className="overflow-x-auto py-2">
                      <table className="w-full min-w-[36rem] text-left text-[13px]">
                        <thead>
                          <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                            {data.table_programme_headers.map((header) => (
                              <th key={header} className="pb-3 pr-3 font-medium">
                                {header}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#f1f5f9]">
                          {data.programmes.map((row) => (
                            <tr key={row.programme_id} className="text-[#374151]">
                              <td className="py-3 pr-3 font-medium text-[#111827]">{row.programme_name}</td>
                              <td className="py-3 pr-3">{row.level_label}</td>
                              <td className="py-3 pr-3 tabular-nums">{row.intake ?? "—"}</td>
                              <td className="py-3 pr-3 tabular-nums">{row.student_count.toLocaleString("en-IN")}</td>
                              <td className="py-3">
                                <StatusPill label={row.status_label} tone={row.status_tone} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="py-6 text-sm text-[#9ca3af]">No programmes mapped to this department yet.</p>
                  )}
                </SectionCard>

                <SectionCard
                  title={data.faculty_section_title}
                  actionHref={data.faculty_allocation_href}
                  actionLabel={data.faculty_allocation_label}
                  footer={
                    <>
                      <span>{data.faculty_footer_label}</span>
                      <Link href={data.faculty_view_all_href} className="font-medium text-[#245dd8] hover:underline">
                        View all →
                      </Link>
                    </>
                  }
                >
                  {data.faculty.length ? (
                    <div className="overflow-x-auto py-2">
                      <table className="w-full min-w-[36rem] text-left text-[13px]">
                        <thead>
                          <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                            {data.table_faculty_headers.map((header) => (
                              <th key={header} className="pb-3 pr-3 font-medium">
                                {header}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#f1f5f9]">
                          {data.faculty.map((row) => (
                            <tr key={row.user_id} className="text-[#374151]">
                              <td className="py-3 pr-3 font-medium text-[#111827]">{row.name}</td>
                              <td className="py-3 pr-3">{row.designation}</td>
                              <td className="py-3 pr-3 tabular-nums">{row.workload_label}</td>
                              <td className="py-3">
                                <StatusPill label={row.status_label} tone={row.status_tone} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="py-6 text-sm text-[#9ca3af]">No faculty assigned to this department yet.</p>
                  )}
                </SectionCard>
              </div>

              <div className="space-y-5">
                <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.resources_section_title}</h3>
                  <ul className="grid grid-cols-2 gap-4">
                    {data.resources.map((item) => (
                      <li key={item.key} className="rounded-lg border border-[#f1f5f9] bg-[#f9fafb] px-3 py-3">
                        <p className="text-[11px] font-medium text-[#6b7280]">{item.title}</p>
                        <p className="mt-1 text-[15px] font-semibold tabular-nums text-[#111827]">{item.value}</p>
                      </li>
                    ))}
                  </ul>
                </section>

                <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.activity_section_title}</h3>
                  <ul className="space-y-4">
                    {data.activities.map((item) => (
                      <li key={item.activity_id} className="flex gap-3">
                        <span
                          className={cn(
                            "mt-1.5 size-2 shrink-0 rounded-full",
                            item.tone === "success"
                              ? "bg-[#10b981]"
                              : item.tone === "warning"
                                ? "bg-[#f97316]"
                                : item.tone === "info"
                                  ? "bg-[#3b82f6]"
                                  : "bg-[#d1d5db]",
                          )}
                        />
                        <div>
                          <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
                          <p className="text-[12px] text-[#9ca3af]">{item.occurred_label}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                </section>
              </div>
            </div>

            <footer className="flex flex-col gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
              <p>{data.footer_disclaimer}</p>
              <p className="tabular-nums">
                {data.footer_snapshot_label} · {formatSnapshot(data.generated_at)}
              </p>
            </footer>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}