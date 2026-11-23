"use client";

import Link from "next/link";
import { useCallback, useMemo, useState, type ReactNode } from "react";
import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { Button } from "@/components/ui/button";
import {
  CollegeAdminChevronDown,
  CollegeAdminDownload,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { fetchDepartments } from "@/features/college-admin/api/organization";
import {
  useDashboardOverview,
  usePendingApprovals,
} from "@/features/college-admin/hooks/use-dashboard";
import { useCampuses } from "@/features/college-admin/hooks/use-institution";
import { CollegeAdminDashboardKpiCard, CollegeAdminKpiGrid } from "@/features/college-admin/components/ui/college-admin-kpi-card";
import {
  CollegeAdminDashboardPanel as Panel,
  CollegeAdminDashboardSideList as SideList,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
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
  const [range, setRange] = useState<DashboardDateRange>("month");
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

  const feeBars = useMemo(
    () =>
      (data?.fee_monthly_collection ?? []).map((m) => ({
        label: m.label.replace(/\s*\(MTD\)$/i, ""),
        value: m.amount_inr,
        mtd: m.is_month_to_date,
      })),
    [data?.fee_monthly_collection],
  );

  const trendPoints = useMemo(
    () =>
      (data?.attendance_trend ?? []).map((p) => ({
        label: p.label,
        students: p.students_pct,
        faculty: p.faculty_pct,
      })),
    [data?.attendance_trend],
  );

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
        <CollegeAdminKpiGrid>
          <CollegeAdminDashboardKpiCard
            label="Total students"
            value={(stats?.total_students ?? 0).toLocaleString("en-IN")}
            hint={`${stats?.active_students ?? 0} active enrolled`}
            kpiKey="total_students"
            index={0}
            iconSlug="graduation-cap"
          />
          <CollegeAdminDashboardKpiCard
            label="Total faculty"
            value={(stats?.faculty_count ?? 0).toLocaleString("en-IN")}
            hint={`${stats?.employee_count ?? 0} total employees`}
            kpiKey="total_faculty"
            index={1}
            iconSlug="users-round"
          />
          <CollegeAdminDashboardKpiCard
            label="Departments"
            value={stats?.department_count ?? 0}
            hint={`${stats?.programme_count ?? 0} active programmes`}
            kpiKey="departments"
            index={2}
            iconSlug="building-2"
          />
          <CollegeAdminDashboardKpiCard
            label="Attendance compliance"
            value={attendancePct != null ? `${attendancePct}%` : "—"}
            hint={`${attendance?.pending_submissions ?? 0} sessions pending`}
            hintTone={(attendance?.pending_submissions ?? 0) > 0 ? "warning" : undefined}
            kpiKey="attendance_compliance"
            index={3}
            iconSlug="clipboard-check"
          />
          <CollegeAdminDashboardKpiCard
            label="Fee collected"
            value={formatMoneyCompact(finance?.collected_amount ?? 0)}
            hint={`${feePct}% of ${formatMoneyCompact(feeTotalDemand)} demand`}
            kpiKey="fee_collected"
            index={4}
            iconSlug="wallet"
          />
          <CollegeAdminDashboardKpiCard
            label="Pending approvals"
            value={data?.pending_approval_count ?? 0}
            hint={`${data?.unresolved_support_count ?? 0} open support items`}
            hintTone={(data?.pending_approval_count ?? 0) > 0 ? "warning" : undefined}
            kpiKey="pending_approvals"
            index={5}
            iconSlug="square-check"
          />
          <CollegeAdminDashboardKpiCard
            label="Scheduled exams"
            value={exams?.scheduled_exams ?? 0}
            hint={`${exams?.pending_evaluations ?? 0} pending evaluations`}
            kpiKey="scheduled_exams"
            index={6}
            iconSlug="file-text"
          />
          <CollegeAdminDashboardKpiCard
            label="Current semester"
            value={term?.semester_label?.replace(/^./, (c) => c.toUpperCase()) ?? "—"}
            hint={term?.academic_year_label ?? "Academic year"}
            kpiKey="current_semester"
            index={7}
            iconSlug="calendar-days"
          />
        </CollegeAdminKpiGrid>

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
              <AttendanceTrendChart
                points={trendPoints}
                footnote="Weekly average attendance % (students vs teaching staff). Change the date filter for a different window."
              />
            </Panel>

            <Panel title="Fee collection by month" actionHref="/college-admin/dashboard/finance-summary">
              <FeeBarChart bars={feeBars} />
            </Panel>
          </div>

          <div className="space-y-4">
            <Panel flushBody title="Pending approvals" actionHref="/college-admin/approvals/pending-approval-requests">
              <SideList
                items={(pendingQ.data?.items ?? []).map((p, i) => ({
                  title: p.title,
                  meta: p.category,
                  badge: i === 0 ? "Up next" : "Pending",
                  badgeTone: i === 0 ? ("primary" as const) : ("warning" as const),
                  iconSlug: i === 0 ? "square-check" : "clock",
                }))}
                empty="No items waiting — you're all caught up."
                emptyTitle="Review approval queue"
                emptyIconSlug="square-check"
                emptyBadgeLabel="Not started"
              />
            </Panel>

            <Panel flushBody title="Upcoming academic events" actionHref="/college-admin/institution/calendar">
              <SideList
                items={(data?.upcoming_events ?? []).slice(0, 5).map((ev) => {
                  const e = ev as { title?: string; event_type?: string; event_at?: string };
                  return {
                    title: String(e.title ?? "Event"),
                    meta: String(e.event_type ?? "Academic"),
                    badge: e.event_at ? formatDate(e.event_at) : undefined,
                  };
                })}
                empty="Nothing scheduled in the selected window."
                emptyTitle="View academic calendar"
                emptyIconSlug="calendar-days"
                emptyBadgeLabel="Not started"
              />
            </Panel>

            <Panel flushBody title="Recent announcements" actionHref="/college-admin/communication/communication-dashboard">
              <SideList
                items={(data?.notifications ?? []).slice(0, 4).map((n) => ({
                  title: n.title,
                  meta: n.message.slice(0, 48) + (n.message.length > 48 ? "…" : ""),
                  iconSlug: "megaphone",
                }))}
                empty="Campus updates will show here when published."
                emptyTitle="Post an announcement"
                emptyIconSlug="megaphone"
                emptyBadgeLabel="Not started"
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

function seriesPolylines(
  points: { students: number | null; faculty: number | null }[],
  value: (p: (typeof points)[number]) => number | null,
  toX: (i: number) => number,
  toY: (v: number) => number,
): string[] {
  const segments: string[] = [];
  let run: string[] = [];
  points.forEach((p, i) => {
    const v = value(p);
    if (v == null || Number.isNaN(v)) {
      if (run.length) {
        segments.push(run.join(" "));
        run = [];
      }
      return;
    }
    run.push(`${toX(i)},${toY(v)}`);
  });
  if (run.length) segments.push(run.join(" "));
  return segments;
}

function AttendanceTrendChart({
  points,
  footnote,
}: {
  points: { label: string; students: number | null; faculty: number | null }[];
  footnote?: string;
}) {
  const plotted = points.filter((p) => p.students != null || p.faculty != null);
  if (plotted.length === 0) {
    return (
      <div className="space-y-3">
        <p className="min-h-[11rem] rounded-lg border border-dashed border-[#e5e7eb] bg-[#f9fafb] px-4 py-8 text-center text-sm text-[#6b7280]">
          No attendance sessions in this range yet. Mark attendance or widen the date filter to see the trend.
        </p>
        {footnote ? <p className="text-[10px] text-[#9ca3af]">{footnote}</p> : null}
      </div>
    );
  }

  const w = 560;
  const h = 200;
  const padLeft = 36;
  const padRight = 16;
  const padY = 28;
  const values = points.flatMap((p) => [p.students, p.faculty].filter((v): v is number => v != null));
  const dataMax = Math.max(...values, 0);
  const dataMin = Math.min(...values, dataMax);
  const yMax = Math.min(100, Math.ceil((dataMax + 4) / 5) * 5);
  const yMin = Math.max(0, Math.floor((Math.min(dataMin, yMax - 12) - 4) / 5) * 5);
  const ySpan = Math.max(yMax - yMin, 8);

  const toX = (i: number) => padLeft + (i / Math.max(points.length - 1, 1)) * (w - padLeft - padRight);
  const toY = (v: number) => h - padY - ((v - yMin) / ySpan) * (h - padY * 2);

  const studentSegments = seriesPolylines(points, (p) => p.students, toX, toY);
  const facultySegments = seriesPolylines(points, (p) => p.faculty, toX, toY);
  const yTicks = [yMin, yMin + ySpan / 2, yMax];

  return (
    <div className="space-y-3">
      <div className="min-h-[12rem] w-full">
        <svg
          viewBox={`0 0 ${w} ${h}`}
          className="h-full min-h-[12rem] w-full"
          preserveAspectRatio="xMidYMid meet"
          role="img"
          aria-label="Attendance trend"
        >
          {yTicks.map((tick) => {
            const y = toY(tick);
            return (
              <g key={tick}>
                <line x1={padLeft} y1={y} x2={w - padRight} y2={y} stroke="#eef2f7" strokeDasharray="4 4" />
                <text x={padLeft - 6} y={y + 3} textAnchor="end" className="fill-[#9ca3af]" fontSize="9">
                  {tick}%
                </text>
              </g>
            );
          })}
          <line x1={padLeft} y1={h - padY} x2={w - padRight} y2={h - padY} stroke="#e8ecf2" />
          {studentSegments.map((seg, idx) => (
            <polyline
              key={`student-${idx}`}
              fill="none"
              stroke="#245dd8"
              strokeWidth="2.5"
              strokeLinejoin="round"
              strokeLinecap="round"
              points={seg}
            />
          ))}
          {facultySegments.map((seg, idx) => (
            <polyline
              key={`faculty-${idx}`}
              fill="none"
              stroke="#93c5fd"
              strokeWidth="2"
              strokeDasharray="6 4"
              strokeLinejoin="round"
              strokeLinecap="round"
              points={seg}
            />
          ))}
        </svg>
      </div>
      <div
        className="grid gap-1 text-center text-[10px] leading-tight text-[#9ca3af]"
        style={{ gridTemplateColumns: `repeat(${points.length}, minmax(0, 1fr))` }}
      >
        {points.map((p) => (
          <span key={p.label} className="truncate px-0.5" title={p.label}>
            {p.label}
          </span>
        ))}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-[#6b7280]">
        <span className="flex items-center gap-1.5">
          <span className="h-0.5 w-4 bg-[#245dd8]" aria-hidden /> Students
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-0.5 w-4 border-t-2 border-dashed border-[#93c5fd]" aria-hidden />{" "}
          Faculty
        </span>
      </div>
      {footnote ? (
        <p className="border-t border-[#f1f5f9] pt-3 text-[11px] leading-relaxed text-[#9ca3af]">
          {footnote}
        </p>
      ) : null}
    </div>
  );
}

function FeeBarChart({ bars }: { bars: { label: string; value: number; mtd?: boolean }[] }) {
  if (bars.length === 0) {
    return (
      <p className="min-h-[12rem] rounded-lg border border-dashed border-[#e5e7eb] bg-[#f9fafb] px-4 py-8 text-center text-sm text-[#6b7280]">
        No verified fee payments recorded for this academic year yet.
      </p>
    );
  }

  const max = Math.max(...bars.map((b) => b.value), 1);
  return (
    <div className="flex min-h-[12rem] items-end justify-between gap-2 pb-1 pt-2">
      {bars.map((b) => {
        const barHeight = Math.max(12, (b.value / max) * 100);
        return (
          <div
            key={b.label}
            className="flex min-h-[10rem] flex-1 flex-col items-center justify-end gap-2"
          >
            <div className="flex h-32 w-full max-w-[52px] items-end justify-center">
              <div
                className={cn(
                  "w-full rounded-t-md transition-[height]",
                  b.mtd ? "bg-[#93c5fd]" : "bg-[#245dd8]",
                )}
                style={{ height: `${barHeight}%`, minHeight: 8 }}
              />
            </div>
            <span className="max-w-full truncate text-center text-[10px] leading-tight text-[#9ca3af]">
              {b.label}
              {b.mtd ? " (MTD)" : ""}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function QuickAction({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="inline-flex items-center rounded-xl border border-[#dce3ec] bg-white px-3.5 py-2 text-[12px] font-semibold text-[#334155] shadow-[0_1px_2px_rgba(15,39,69,0.05)] transition-colors hover:border-[#c7dafc] hover:bg-[#f4f8ff] hover:text-[#245dd8]"
    >
      {children}
    </Link>
  );
}