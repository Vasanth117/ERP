"use client";

import Link from "next/link";
import { CollegeAdminDashboardPanel as Panel } from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { useCallback, useMemo, useState, type ReactNode } from "react";
import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { Button } from "@/components/ui/button";
import {
  CollegeAdminChevronDown,
  CollegeAdminDownload,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { fetchDepartments } from "@/features/college-admin/api/organization";
import { CollegeAdminDashboardKpiCard, CollegeAdminKpiGrid } from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useFacultyStatisticsOverview } from "@/features/college-admin/hooks/use-faculty-statistics";
import type { DashboardDateRange } from "@/features/college-admin/types/dashboard";
import type { DistributionItem } from "@/features/college-admin/types/student-statistics";
import { cn } from "@/lib/utils";

const RANGE_OPTIONS: { value: DashboardDateRange; label: string }[] = [
  { value: "today", label: "Today" },
  { value: "week", label: "This week" },
  { value: "month", label: "This month" },
  { value: "semester", label: "This semester" },
];


function formatJoined(iso: string | null | undefined) {
  if (!iso) return "—";
  try {
    return new Intl.DateTimeFormat("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function titleCaseDesignation(value: string) {
  return value
    .split(" ")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}


function DepartmentBarChart({
  items,
}: {
  items: { label: string; count: number }[];
}) {
  const max = Math.max(...items.map((i) => i.count), 1);
  if (!items.length) {
    return <p className="text-sm text-[#9ca3af]">No faculty assigned to departments yet.</p>;
  }
  return (
    <div className="flex h-44 items-end justify-between gap-1 overflow-x-auto pb-1">
      {items.map((item) => (
        <div
          key={item.label}
          className="flex min-w-[2.25rem] flex-1 flex-col items-center gap-1"
        >
          <span className="text-[10px] font-medium tabular-nums text-[#6b7280]">
            {item.count}
          </span>
          <div
            className="w-full max-w-[40px] rounded-t-md bg-[#245dd8]"
            style={{ height: `${Math.max(10, (item.count / max) * 100)}%` }}
          />
          <span className="max-w-[3rem] truncate text-[9px] text-[#9ca3af]" title={item.label}>
            {item.label}
          </span>
        </div>
      ))}
    </div>
  );
}

function MixBars({ items }: { items: DistributionItem[] }) {
  if (!items.length) {
    return <p className="text-sm text-[#9ca3af]">No data for the selected filters.</p>;
  }
  const max = Math.max(...items.map((i) => i.count), 1);
  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li key={item.key}>
          <div className="mb-1 flex items-center justify-between gap-2 text-[12px]">
            <span className="font-medium text-[#374151]">{item.label}</span>
            <span className="shrink-0 tabular-nums text-[#6b7280]">
              {item.count.toLocaleString("en-IN")}
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-[#eef2f7]">
            <div
              className="h-full rounded-full bg-[#245dd8]"
              style={{ width: `${Math.max(4, (item.count / max) * 100)}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

function OnboardingBadge({ status, label }: { status: string; label: string }) {
  const styles =
    status === "completed"
      ? "bg-[#ecfdf5] text-[#047857]"
      : status === "documents_due"
        ? "bg-[#fff7ed] text-[#c2410c]"
        : "bg-[#eff6ff] text-[#1d4ed8]";
  return (
    <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles)}>
      {label}
    </span>
  );
}

function AvailabilityBadge({ statusKey, count }: { statusKey: string; count: number }) {
  const styles =
    statusKey === "present"
      ? "bg-[#ecfdf5] text-[#047857]"
      : statusKey === "on_leave"
        ? "bg-[#eff6ff] text-[#1d4ed8]"
        : "bg-[#fff7ed] text-[#c2410c]";
  return (
    <span
      className={cn(
        "inline-flex h-9 min-w-9 shrink-0 items-center justify-center rounded-full px-2 text-[12px] font-semibold leading-none tabular-nums",
        styles,
      )}
    >
      {count.toLocaleString("en-IN")}
    </span>
  );
}

function FilterSelect({
  value,
  onChange,
  active,
  children,
  disabled,
  "aria-label": ariaLabel,
  className,
  leadingIcon,
}: {
  value: string;
  onChange: (value: string) => void;
  active?: boolean;
  children: ReactNode;
  disabled?: boolean;
  "aria-label"?: string;
  className?: string;
  leadingIcon?: ReactNode;
}) {
  return (
    <div className={cn("relative inline-flex min-w-[8.75rem]", className)}>
      {leadingIcon ? (
        <span
          className={cn(
            "pointer-events-none absolute left-2.5 top-1/2 z-[1] -translate-y-1/2",
            active ? "text-[#245dd8]" : "text-[#6b7280]",
          )}
          aria-hidden
        >
          {leadingIcon}
        </span>
      ) : null}
      <select
        aria-label={ariaLabel}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          "w-full min-w-[8.75rem] cursor-pointer appearance-none truncate rounded-md border py-1.5 pr-8 text-xs outline-none transition-colors",
          leadingIcon ? "pl-8" : "pl-3",
          active
            ? "border-[#245dd8] bg-[#eef4ff] font-medium text-[#245dd8]"
            : "border-[#e5e7eb] bg-white text-[#374151]",
          disabled && "cursor-not-allowed opacity-60",
        )}
      >
        {children}
      </select>
      <CollegeAdminChevronDown
        className={cn(
          "pointer-events-none absolute right-2 top-1/2 size-3.5 -translate-y-1/2",
          active ? "text-[#245dd8]" : "text-[#6b7280]",
        )}
        aria-hidden
      />
    </div>
  );
}

export function FacultyStatisticsDashboard() {
  const [range, setRange] = useState<DashboardDateRange>("today");
  const [departmentId, setDepartmentId] = useState("");
  const [designation, setDesignation] = useState("");

  const queryParams = useMemo(
    () => ({
      range,
      ...(departmentId ? { department_id: departmentId } : {}),
      ...(designation ? { designation } : {}),
    }),
    [range, departmentId, designation],
  );

  const { data, isLoading, isError, error, refetch, isFetching } =
    useFacultyStatisticsOverview(queryParams);

  const departmentsQ = useQuery({
    queryKey: ["college-admin", "departments", "faculty-stats"],
    queryFn: fetchDepartments,
  });

  const kpis = data?.kpis;

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `faculty-statistics-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const deptChart = useMemo(
    () =>
      (data?.faculty_by_department ?? []).map((d) => ({
        label: d.department_code,
        count: d.faculty_count,
      })),
    [data?.faculty_by_department],
  );

  const ratioHint = useMemo(() => {
    if (!kpis?.regulatory_ratio_max) return null;
    const label = kpis.regulatory_ratio_label ?? "Regulatory norm";
    return `${label} ${kpis.regulatory_ratio_max} : 1`;
  }, [kpis]);

  const designationOptions = data?.designation_filter_options ?? [];

  return (
    <div className="space-y-5" data-figma-frame="65:1116">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            Faculty & employee statistics
          </h2>
          <p className="mt-1 max-w-2xl text-[14px] leading-relaxed text-[#6b7280]">
            Teaching and non-teaching workforce, qualifications and availability
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <Button
            type="button"
            className="h-9 gap-1.5 border border-[#245dd8] bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8]"
            onClick={handleExport}
            disabled={isLoading || !data}
          >
            <CollegeAdminDownload className="size-3.5" />
            Export
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <FilterSelect
          value={range}
          onChange={(v) => setRange(v as DashboardDateRange)}
          active={range === "today"}
          aria-label="Snapshot range"
          className="min-w-[8.5rem]"
          leadingIcon={<CalendarIcon className="size-3.5" />}
        >
          {RANGE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </FilterSelect>

        <FilterSelect
          value={departmentId}
          onChange={setDepartmentId}
          active={Boolean(departmentId)}
          aria-label="Department"
          className="min-w-[11.5rem]"
          leadingIcon={<FilterIcon className="size-3.5" />}
          disabled={departmentsQ.isLoading}
        >
          <option value="">All departments</option>
          {(departmentsQ.data ?? []).map((d) => (
            <option key={d.department_id} value={d.department_id}>
              {d.name}
            </option>
          ))}
        </FilterSelect>

        <FilterSelect
          value={designation}
          onChange={setDesignation}
          active={Boolean(designation)}
          aria-label="Designation"
          className="min-w-[11.5rem]"
          leadingIcon={<FilterIcon className="size-3.5" />}
          disabled={isLoading && !designationOptions.length}
        >
          <option value="">All designations</option>
          {designationOptions.map((d) => (
            <option key={d} value={d}>
              {titleCaseDesignation(d)}
            </option>
          ))}
        </FilterSelect>

      </div>

      <QueryState
        isLoading={isLoading || isFetching}
        isError={isError}
        error={error}
        onRetry={() => void refetch()}
      >
        {data ? (
          <>
            <CollegeAdminKpiGrid>
              <CollegeAdminDashboardKpiCard
                label="Teaching faculty"
                value={kpis?.teaching_faculty_total.toLocaleString("en-IN") ?? 0}
                hint={`${kpis?.teaching_faculty_regular ?? 0} regular · ${kpis?.teaching_faculty_visiting ?? 0} visiting`}
              />
              <CollegeAdminDashboardKpiCard
                label="Non-teaching staff"
                value={kpis?.non_teaching_staff_total.toLocaleString("en-IN") ?? 0}
                hint={kpis?.non_teaching_staff_detail ?? "Admin, technical & support"}
              />
              <CollegeAdminDashboardKpiCard
                label="Student-faculty ratio"
                value={kpis?.student_faculty_ratio_display ?? "—"}
                hint={ratioHint ?? "Based on enrolled students and teaching faculty"}
                hintTone={kpis?.regulatory_ratio_meets_norm === true ? "success" : "muted"}
              />
              <CollegeAdminDashboardKpiCard
                label="Open positions"
                value={kpis?.open_positions_total ?? 0}
                hint={`${kpis?.open_positions_teaching ?? 0} teaching · ${kpis?.open_positions_non_teaching ?? 0} non-teaching`}
                hintTone="warning"
              />
            </CollegeAdminKpiGrid>

            <div className="grid gap-4 xl:grid-cols-3">
              <div className="space-y-4 xl:col-span-2">
                <Panel
                  title="Faculty by department"
                  actionHref="/college-admin/faculty/faculty-directory"
                  actionLabel="Faculty directory →"
                >
                  <DepartmentBarChart items={deptChart} />
                </Panel>

                <Panel
                  title="Recently joined"
                  actionHref="/college-admin/faculty/employee-directory"
                  actionLabel="Employee directory →"
                >
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[32rem] text-left text-[12px]">
                      <thead>
                        <tr className="border-b border-[#e8ecf2] text-[#6b7280]">
                          <th className="pb-2 pr-3 font-medium">Name</th>
                          <th className="pb-2 px-2 font-medium">Designation</th>
                          <th className="pb-2 px-2 font-medium">Department</th>
                          <th className="pb-2 px-2 font-medium">Joined</th>
                          <th className="pb-2 pl-2 font-medium">Onboarding</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.recently_joined.length ? (
                          data.recently_joined.map((row) => (
                            <tr
                              key={row.user_id}
                              className="border-b border-[#f1f5f9] text-[#111827]"
                            >
                              <td className="py-2.5 pr-3 font-medium">{row.full_name}</td>
                              <td className="px-2 py-2.5">{row.designation ?? "—"}</td>
                              <td className="px-2 py-2.5">{row.department_name ?? "—"}</td>
                              <td className="px-2 py-2.5 tabular-nums">
                                {formatJoined(row.joined_on)}
                              </td>
                              <td className="py-2.5 pl-2">
                                <OnboardingBadge
                                  status={row.onboarding_status}
                                  label={row.onboarding_label}
                                />
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan={5} className="py-6 text-center text-[#9ca3af]">
                              No joiners in the selected window.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                  <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] pt-3 text-[11px] text-[#6b7280]">
                    <span>
                      {data.recently_joined_count} joiners in the last{" "}
                      {data.recently_joined_window_days} days
                    </span>
                    <Link
                      href="/college-admin/faculty/employee-directory"
                      className="font-medium text-[#245dd8] hover:underline"
                    >
                      View all →
                    </Link>
                  </div>
                </Panel>
              </div>

              <div className="space-y-4">
                <Panel title="Faculty qualifications">
                  <MixBars items={data.qualification_mix} />
                </Panel>

                <Panel title="Designation mix">
                  <MixBars items={data.designation_mix} />
                </Panel>

                <Panel
                  title="Availability today"
                  actionHref="/college-admin/dashboard/attendance-overview"
                  actionLabel="Attendance →"
                >
                  <ul className="divide-y divide-[#f1f5f9]">
                    {data.availability_today.map((row) => (
                      <li key={row.status_key} className="flex items-center gap-3 py-3 first:pt-0">
                        <AvailabilityBadge statusKey={row.status_key} count={row.count} />
                        <div className="min-w-0 flex-1">
                          <p className="text-[13px] font-semibold text-[#111827]">{row.label}</p>
                          <p className="text-[11px] text-[#9ca3af]">{row.description}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                </Panel>
              </div>
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}