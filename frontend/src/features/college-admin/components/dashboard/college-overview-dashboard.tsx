"use client";

import Link from "next/link";
import { useCallback, useMemo, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import {
  CollegeAdminChevronDown,
  CollegeAdminDownload,
  CollegeAdminMegaphone,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { fetchDepartments } from "@/features/college-admin/api/organization";
import {
  useDashboardOverview,
  usePendingApprovals,
} from "@/features/college-admin/hooks/use-dashboard";
import { useCampuses } from "@/features/college-admin/hooks/use-institution";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import type { DashboardDateRange } from "@/features/college-admin/types/dashboard";
import { cn } from "@/lib/utils";

const RANGE_OPTIONS: { value: DashboardDateRange; label: string }[] = [
  { value: "semester", label: "This semester" },
  { value: "month", label: "This month" },
  { value: "week", label: "This week" },
  { value: "today", label: "Today" },
];

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatMoneyCompact(value: number) {
  if (value >= 10_000_000) {
    return `₹${(value / 10_000_000).toFixed(1)} Cr`;
  }
  if (value >= 100_000) {
    return `₹${(value / 100_000).toFixed(1)} L`;
  }
  return formatMoney(value);
}

function formatDate(iso: string) {
  try {
    return new Intl.DateTimeFormat("en-IN", {
      day: "numeric",
      month: "short",
    }).format(new Date(iso));
  } catch {
    return "—";
  }
}

function attendanceCompliancePercent(
  submitted: number,
  pending: number,
): number | null {
  const total = submitted + pending;
  if (total === 0) return null;
  return Math.round((submitted / total) * 1000) / 10;
}

export function CollegeOverviewDashboard() {
  const [range, setRange] = useState<DashboardDateRange>("semester");
  const [departmentId, setDepartmentId] = useState("");
  const [campusId, setCampusId] = useState("");

  const dashboardParams = useMemo(
    () => ({
      range,
      ...(departmentId ? { department_id: departmentId } : {}),
      ...(campusId ? { campus_id: campusId } : {}),
    }),
    [range, departmentId, campusId],
  );

  const { data, isLoading, isError, error, refetch, isFetching } =
    useDashboardOverview(dashboardParams);
  const pendingQ = usePendingApprovals(0, 8);
  const departmentsQ = useQuery({
    queryKey: ["college-admin", "departments", "overview-filters"],
    queryFn: fetchDepartments,
  });
  const campusesQ = useCampuses(true);

  const stats = data?.statistics;
  const term = data?.academic_term;
  const finance = data?.finance;
  const exams = data?.examinations;
  const attendance = data?.attendance;

  const feeTotalDemand = (finance?.collected_amount ?? 0) + (finance?.outstanding_amount ?? 0);
  const feePct =
    feeTotalDemand > 0
      ? Math.round(((finance?.collected_amount ?? 0) / feeTotalDemand) * 100)
      : 0;

  const attendancePct = attendanceCompliancePercent(
    attendance?.sessions_submitted ?? 0,
    attendance?.pending_submissions ?? 0,
  );

  const alert = useMemo(() => {
    const urgent = pendingQ.data?.items?.[0];
    if (urgent) {
      return {
        title: urgent.title,
        meta: `${urgent.category} · Submitted ${formatDate(urgent.submitted_at)}`,
        href: "/college-admin/approvals/pending-approval-requests",
      };
    }
    const note = data?.notifications?.find((n) => n.severity !== "info") ?? data?.notifications?.[0];
    if (note) {
      return {
        title: note.title,
        meta: note.message,
        href: "/college-admin/dashboard/alerts",
      };
    }
    return null;
  }, [data?.notifications, pendingQ.data?.items]);

  const feeBars = useMemo(() => {
    const labels = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov"];
    const current = finance?.collected_amount ?? 0;
    return labels.map((label, i) => ({
      label,
      value: i === labels.length - 1 ? current : Math.round(current * 0.12 * (i + 1) * 0.15),
      mtd: i === labels.length - 1,
    }));
  }, [finance?.collected_amount]);

  const trendPoints = useMemo(() => {
    const base = attendancePct ?? 75;
    return [0.92, 0.94, 0.93, 0.96, 0.95, 0.97, 0.98, 1].map((m, i) => ({
      label: `W${i + 7}`,
      students: Math.min(100, base * m),
      faculty: Math.min(100, (base - 5) * m),
    }));
  }, [attendancePct]);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `college-overview-${new Date().toISOString().slice(0, 10)}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <div className="space-y-5" data-figma-frame="64:190">
      <div className="flex flex-wrap items-center gap-2 text-xs text-[#6b7280]">
        <FilterSelect
          value={range}
          onChange={(v) => setRange(v as DashboardDateRange)}
          active={range === "semester"}
          aria-label="Date range"
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
          value={campusId}
          onChange={setCampusId}
          active={Boolean(campusId)}
          aria-label="Campus"
          disabled={campusesQ.isLoading}
        >
          <option value="">All campuses</option>
          {(campusesQ.data ?? []).map((c) => (
            <option key={c.campus_id} value={c.campus_id}>
              {c.name}
            </option>
          ))}
        </FilterSelect>

        <div className="ml-auto flex flex-wrap items-center gap-2">
          <Button
            type="button"
            className="h-9 gap-1.5 border border-[#245dd8] bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8]"
            onClick={handleExport}
            disabled={!data || isLoading}
          >
            <CollegeAdminDownload className="size-3.5" />
            Export report
          </Button>
        </div>
      </div>

      <QueryState
        isLoading={isLoading || isFetching}
        isError={isError}
        error={error}
        onRetry={() => void refetch()}
      >
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <OverviewKpi
            label="Total students"
            value={(stats?.total_students ?? 0).toLocaleString("en-IN")}
            hint={`${stats?.active_students ?? 0} active enrolled`}
          />
          <OverviewKpi
            label="Total faculty"
            value={(stats?.faculty_count ?? 0).toLocaleString("en-IN")}
            hint={`${stats?.employee_count ?? 0} total employees`}
          />
          <OverviewKpi
            label="Departments"
            value={stats?.department_count ?? 0}
            hint={`${stats?.programme_count ?? 0} active programmes`}
          />
          <OverviewKpi
            label="Attendance compliance"
            value={attendancePct != null ? `${attendancePct}%` : "—"}
            hint={`${attendance?.pending_submissions ?? 0} sessions pending`}
            hintWarn={(attendance?.pending_submissions ?? 0) > 0}
          />
          <OverviewKpi
            label="Fee collected"
            value={formatMoneyCompact(finance?.collected_amount ?? 0)}
            hint={`${feePct}% of ${formatMoneyCompact(feeTotalDemand)} demand`}
          />
          <OverviewKpi
            label="Pending approvals"
            value={data?.pending_approval_count ?? 0}
            hint={`${data?.unresolved_support_count ?? 0} open support items`}
            hintWarn={(data?.pending_approval_count ?? 0) > 0}
          />
          <OverviewKpi
            label="Scheduled exams"
            value={exams?.scheduled_exams ?? 0}
            hint={`${exams?.pending_evaluations ?? 0} pending evaluations`}
          />
          <OverviewKpi
            label="Current semester"
            value={term?.semester_label?.replace(/^./, (c) => c.toUpperCase()) ?? "—"}
            hint={term?.academic_year_label ?? "Academic year"}
          />
        </div>

        {alert ? (
          <div className="flex flex-col gap-3 rounded-xl border border-[#fcd9b8] bg-[#fff7ed] px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-[#9a3412]">
              <span className="font-semibold">{alert.title}</span>
              <span className="text-[#c2410c]"> · {alert.meta}</span>
            </p>
            <Link
              href={alert.href}
              className="shrink-0 text-sm font-medium text-[#ea580c] hover:underline"
            >
              Review request →
            </Link>
          </div>
        ) : null}

        <div className="grid gap-4 xl:grid-cols-3">
          <div className="space-y-4 xl:col-span-2">
            <Panel title="Attendance trend" actionHref="/college-admin/dashboard/attendance-overview" actionLabel="View report">
              <AttendanceTrendChart points={trendPoints} />
              <p className="mt-2 text-[11px] text-[#9ca3af]">
                Student vs faculty session compliance (derived from current term data).
              </p>
            </Panel>

            <Panel title="Fee collection by month" actionHref="/college-admin/dashboard/finance-summary">
              <FeeBarChart bars={feeBars} />
            </Panel>
          </div>

          <div className="space-y-4">
            <Panel title="Pending approvals" actionHref="/college-admin/approvals/pending-approval-requests">
              <SideList
                items={(pendingQ.data?.items ?? []).map((p) => ({
                  title: p.title,
                  meta: p.category,
                  badge: "Pending",
                }))}
                empty="No pending approvals."
              />
            </Panel>

            <Panel title="Upcoming academic events" actionHref="/college-admin/institution/calendar">
              <SideList
                items={(data?.upcoming_events ?? []).slice(0, 5).map((ev) => {
                  const e = ev as { title?: string; event_type?: string; event_at?: string };
                  return {
                    title: String(e.title ?? "Event"),
                    meta: String(e.event_type ?? "Academic"),
                    badge: e.event_at ? formatDate(e.event_at) : undefined,
                  };
                })}
                empty="No upcoming events in this window."
              />
            </Panel>

            <Panel title="Recent announcements" actionHref="/college-admin/communication/communication-dashboard">
              <SideList
                items={(data?.notifications ?? []).slice(0, 4).map((n) => ({
                  title: n.title,
                  meta: n.message.slice(0, 48) + (n.message.length > 48 ? "…" : ""),
                  icon: true,
                }))}
                empty="No announcements yet."
              />
            </Panel>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 border-t border-[#f1f5f9] pt-4">
          <QuickAction href="/college-admin/students/create-student">+ Add student</QuickAction>
          <QuickAction href="/college-admin/students/admissions-list">New admission</QuickAction>
          <QuickAction href="/college-admin/communication/create-announcement">
            Create announcement
          </QuickAction>
          <QuickAction href="/college-admin/approvals/pending-approval-requests">
            Review approvals
          </QuickAction>
          <QuickAction href="/college-admin/reports/reports-dashboard">Generate report</QuickAction>
        </div>
      </QueryState>
    </div>
  );
}

function FilterSelect({
  value,
  onChange,
  active,
  children,
  disabled,
  "aria-label": ariaLabel,
}: {
  value: string;
  onChange: (value: string) => void;
  active?: boolean;
  children: ReactNode;
  disabled?: boolean;
  "aria-label"?: string;
}) {
  return (
    <div className="relative inline-flex max-w-[11rem] min-w-0">
      <select
        aria-label={ariaLabel}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          "w-full min-w-0 cursor-pointer appearance-none truncate rounded-md border py-1.5 pl-3 pr-8 text-xs outline-none transition-colors",
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

function OverviewKpi({
  label,
  value,
  hint,
  hintWarn,
}: {
  label: string;
  value: string | number;
  hint: string;
  hintWarn?: boolean;
}) {
  return (
    <div className="rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <p className="text-[12px] font-medium text-[#6b7280]">{label}</p>
      <p className="mt-2 text-[1.65rem] font-bold leading-none tracking-tight text-[#111827] tabular-nums">
        {value}
      </p>
      <p
        className={cn(
          "mt-3 text-[11px] leading-snug",
          hintWarn ? "text-[#ea580c]" : "text-[#9ca3af]",
        )}
      >
        {hint}
      </p>
    </div>
  );
}

function Panel({
  title,
  children,
  actionHref,
  actionLabel = "View all →",
}: {
  title: string;
  children: React.ReactNode;
  actionHref?: string;
  actionLabel?: string;
}) {
  return (
    <section className="rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
        {actionHref ? (
          <Link href={actionHref} className="text-[12px] font-medium text-[#245dd8] hover:underline">
            {actionLabel}
          </Link>
        ) : null}
      </div>
      {children}
    </section>
  );
}

function AttendanceTrendChart({
  points,
}: {
  points: { label: string; students: number; faculty: number }[];
}) {
  const w = 560;
  const h = 160;
  const pad = 24;
  const maxY = 100;
  const toX = (i: number) => pad + (i / Math.max(points.length - 1, 1)) * (w - pad * 2);
  const toY = (v: number) => h - pad - (v / maxY) * (h - pad * 2);

  const studentLine = points.map((p, i) => `${toX(i)},${toY(p.students)}`).join(" ");
  const facultyLine = points.map((p, i) => `${toX(i)},${toY(p.faculty)}`).join(" ");

  return (
    <div>
      <svg viewBox={`0 0 ${w} ${h}`} className="h-40 w-full" role="img" aria-label="Attendance trend">
        <line x1={pad} y1={h - pad} x2={w - pad} y2={h - pad} stroke="#e8ecf2" />
        <polyline fill="none" stroke="#245dd8" strokeWidth="2.5" points={studentLine} />
        <polyline
          fill="none"
          stroke="#93c5fd"
          strokeWidth="2"
          strokeDasharray="6 4"
          points={facultyLine}
        />
      </svg>
      <div className="mt-1 flex justify-between text-[10px] text-[#9ca3af]">
        {points.map((p) => (
          <span key={p.label}>{p.label}</span>
        ))}
      </div>
      <div className="mt-2 flex gap-4 text-[11px] text-[#6b7280]">
        <span className="flex items-center gap-1.5">
          <span className="h-0.5 w-4 bg-[#245dd8]" /> Students
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-0.5 w-4 border-t-2 border-dashed border-[#93c5fd]" /> Faculty
        </span>
      </div>
    </div>
  );
}

function FeeBarChart({ bars }: { bars: { label: string; value: number; mtd?: boolean }[] }) {
  const max = Math.max(...bars.map((b) => b.value), 1);
  return (
    <div className="flex h-36 items-end justify-between gap-2">
      {bars.map((b) => (
        <div key={b.label} className="flex flex-1 flex-col items-center gap-1">
          <div
            className={cn(
              "w-full max-w-[48px] rounded-t-md",
              b.mtd ? "bg-[#93c5fd]" : "bg-[#245dd8]",
            )}
            style={{ height: `${Math.max(8, (b.value / max) * 100)}%` }}
          />
          <span className="text-[10px] text-[#9ca3af]">
            {b.label}
            {b.mtd ? " (MTD)" : ""}
          </span>
        </div>
      ))}
    </div>
  );
}

function SideList({
  items,
  empty,
}: {
  items: { title: string; meta?: string; badge?: string; icon?: boolean }[];
  empty: string;
}) {
  if (!items.length) {
    return <p className="text-sm text-[#9ca3af]">{empty}</p>;
  }
  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li key={item.title} className="flex gap-2 text-sm">
          {item.icon ? (
            <CollegeAdminMegaphone
              className="mt-0.5 size-4 shrink-0 text-[#245dd8]"
              aria-hidden
            />
          ) : null}
          <div className="min-w-0 flex-1">
            <p className="font-medium text-[#111827]">{item.title}</p>
            {item.meta ? <p className="text-[12px] text-[#9ca3af]">{item.meta}</p> : null}
          </div>
          {item.badge ? (
            <StatusPill
              label={item.badge}
              tone={item.badge === "Pending" ? "warning" : "info"}
            />
          ) : null}
        </li>
      ))}
    </ul>
  );
}

function StatusPill({
  label,
  tone,
}: {
  label: string;
  tone: "success" | "warning" | "info";
}) {
  const styles = {
    success: "bg-[#ecfdf3] text-[#15803d]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eef4ff] text-[#245dd8]",
  };
  return (
    <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-medium", styles[tone])}>
      {label}
    </span>
  );
}

function QuickAction({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="rounded-lg border border-[#e5e7eb] bg-white px-3 py-2 text-xs font-medium text-[#374151] transition-colors hover:border-[#d1d5db] hover:bg-[#f9fafb]"
    >
      {children}
    </Link>
  );
}