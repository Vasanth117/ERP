"use client";

import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import {
  QueryState,
  StatCard,
} from "@/features/college-admin/components/ui/query-state";
import { PageHeading } from "@/features/college-admin/components/layout/page-heading";
import {
  useDashboardOverview,
  useDashboardStatistics,
  useOperationalSummaries,
  usePendingApprovals,
  useRecentActivities,
} from "@/features/college-admin/hooks/use-dashboard";

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function DashboardOverviewView() {
  const { data, isLoading, isError, error, refetch, isFetching } =
    useDashboardOverview({ range: "week" });

  const term = data?.academic_term;
  const stats = data?.statistics;

  return (
    <div data-figma-frame="64:190">
      <PageHeading
        title="College Admin Dashboard"
        description="Operational snapshot across students, academics, finance and campus services."
        figmaFrame="64:190"
        onRefresh={() => void refetch()}
        actions={
          <Button className="h-9 bg-[#245dd8] text-xs hover:bg-[#1f4fb8]">
            Download report
          </Button>
        }
      />
      <QueryState
        isLoading={isLoading || isFetching}
        isError={isError}
        error={error}
        onRetry={() => void refetch()}
      >
        <div className="mb-4 flex flex-wrap gap-2 text-xs text-[#607086]">
          <span className="rounded border border-[#dce3ec] bg-white px-3 py-2">
            Range: {data?.filters.date_range ?? "week"}
          </span>
          {term?.academic_year_label ? (
            <span className="rounded border border-[#dce3ec] bg-white px-3 py-2">
              {term.academic_year_label}
              {term.semester_label ? ` · ${term.semester_label}` : ""}
            </span>
          ) : null}
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <StatCard label="Total students" value={stats?.total_students ?? 0} />
          <StatCard label="Active students" value={stats?.active_students ?? 0} />
          <StatCard label="Faculty" value={stats?.faculty_count ?? 0} />
          <StatCard label="Employees" value={stats?.employee_count ?? 0} />
          <StatCard label="Departments" value={stats?.department_count ?? 0} />
          <StatCard label="Programmes" value={stats?.programme_count ?? 0} />
        </div>
        <SectionPanel title="Operations" className="mt-6">
          <OperationsGrid
            attendance={data?.attendance}
            exams={data?.examinations}
            finance={data?.finance}
            library={data?.library_hostel}
            pending={data?.pending_approval_count}
            support={data?.unresolved_support_count}
          />
        </SectionPanel>
        {data?.notifications?.length ? (
          <SectionPanel title="Important alerts" className="mt-6">
            <ul className="divide-y divide-[#eceff4]">
              {data.notifications.map((n, idx) => (
                <li key={`${n.title}-${idx}`} className="py-3 text-sm">
                  <p className="font-medium text-[#172b45]">{n.title}</p>
                  <p className="text-[#607086]">{n.message}</p>
                </li>
              ))}
            </ul>
          </SectionPanel>
        ) : null}
      </QueryState>
    </div>
  );
}

function SectionPanel({
  title,
  className,
  children,
}: {
  title: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <section
      className={`rounded-xl border border-[#dce3ec] bg-white p-5 shadow-[0px_1px_1px_rgba(23,43,69,0.04)] ${className ?? ""}`}
    >
      <h2 className="text-sm font-semibold text-[#172b45]">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function OperationsGrid({
  attendance,
  exams,
  finance,
  library,
  pending,
  support,
}: {
  attendance?: {
    sessions_submitted: number;
    pending_submissions: number;
    correction_requests_open: number;
  };
  exams?: {
    scheduled_exams: number;
    pending_evaluations: number;
    published_results: number;
  };
  finance?: {
    collected_amount: number;
    outstanding_amount: number;
    open_demands: number;
    overdue_demands: number;
  };
  library?: {
    catalog_items: number;
    active_circulation: number;
    open_fines: number;
    hostel_allocations: number;
    pending_hostel_applications: number;
  };
  pending?: number;
  support?: number;
}) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <StatCard
        label="Attendance sessions"
        value={attendance?.sessions_submitted ?? 0}
        hint={`${attendance?.pending_submissions ?? 0} pending`}
      />
      <StatCard
        label="Scheduled exams"
        value={exams?.scheduled_exams ?? 0}
        hint={`${exams?.pending_evaluations ?? 0} pending evaluations`}
      />
      <StatCard
        label="Fees collected"
        value={formatMoney(finance?.collected_amount ?? 0)}
        hint={`Outstanding ${formatMoney(finance?.outstanding_amount ?? 0)}`}
      />
      <StatCard
        label="Pending approvals"
        value={pending ?? 0}
        hint={`${support ?? 0} open support items`}
      />
      <StatCard
        label="Library circulation"
        value={library?.active_circulation ?? 0}
        hint={`${library?.catalog_items ?? 0} catalogue items`}
      />
      <StatCard
        label="Hostel allocations"
        value={library?.hostel_allocations ?? 0}
        hint={`${library?.pending_hostel_applications ?? 0} applications`}
      />
    </div>
  );
}

export function InstitutionalOverviewDashboardView() {
  const q = useDashboardStatistics();
  return (
    <DashboardStatsShell
      frame="65:185"
      title="Institutional overview"
      query={q}
      emphasis="departments"
    />
  );
}

export function StudentStatisticsView() {
  const q = useDashboardStatistics();
  return (
    <DashboardStatsShell
      frame="65:618"
      title="Student statistics"
      query={q}
      emphasis="students"
    />
  );
}

export function FacultyStatisticsView() {
  const q = useDashboardStatistics();
  return (
    <DashboardStatsShell
      frame="65:1116"
      title="Faculty & employee statistics"
      query={q}
      emphasis="faculty"
    />
  );
}

export function DepartmentPerformanceView() {
  const q = useDashboardStatistics();
  return (
    <DashboardStatsShell
      frame="65:1592"
      title="Department performance"
      query={q}
      emphasis="departments"
    />
  );
}

export function AcademicAnalyticsView() {
  const q = useOperationalSummaries();
  return <OperationalView frame="66:1973" title="Academic performance" query={q} />;
}

export function AttendanceOverviewView() {
  const q = useOperationalSummaries();
  return <OperationalView frame="66:2485" title="Attendance overview" query={q} section="attendance" />;
}

export function ExaminationOverviewView() {
  const q = useOperationalSummaries();
  return <OperationalView frame="66:2970" title="Examination overview" query={q} section="exams" />;
}

export function FinanceSummaryView() {
  const q = useOperationalSummaries();
  return <OperationalView frame="66:3440" title="Finance summary" query={q} section="finance" />;
}

export function PendingApprovalsView() {
  const q = usePendingApprovals();
  return (
    <div data-figma-frame="67:3905">
      <PageHeading title="Pending approvals dashboard" figmaFrame="67:3905" />
      <QueryState
        isLoading={q.isLoading}
        isError={q.isError}
        error={q.error}
        isEmpty={!q.data?.items.length}
        emptyMessage="No pending approvals."
        onRetry={() => void q.refetch()}
      >
        <ul className="divide-y rounded-xl border border-[#dce3ec] bg-white">
          {q.data?.items.map((item) => (
            <li key={item.reference_id} className="px-4 py-3 text-sm">
              <p className="font-medium text-[#172b45]">{item.title}</p>
              <p className="text-[#607086]">
                {item.category} · {new Date(item.submitted_at).toLocaleString()}
              </p>
            </li>
          ))}
        </ul>
      </QueryState>
    </div>
  );
}

export function RecentActivitiesView() {
  const q = useRecentActivities();
  return (
    <div data-figma-frame="67:4394">
      <PageHeading title="Recent institutional activities" figmaFrame="67:4394" />
      <QueryState
        isLoading={q.isLoading}
        isError={q.isError}
        error={q.error}
        isEmpty={!q.data?.items.length}
        onRetry={() => void q.refetch()}
      >
        <ul className="divide-y rounded-xl border border-[#dce3ec] bg-white">
          {q.data?.items.map((item) => (
            <li key={item.activity_id} className="px-4 py-3 text-sm">
              <p className="font-medium text-[#172b45]">{item.title}</p>
              <p className="text-[#607086]">
                {item.actor_label ?? "System"} ·{" "}
                {new Date(item.occurred_at).toLocaleString()}
              </p>
            </li>
          ))}
        </ul>
      </QueryState>
    </div>
  );
}

export function AlertsDashboardView() {
  const { data, isLoading, isError, error, refetch } = useDashboardOverview();
  return (
    <div data-figma-frame="67:4882">
      <PageHeading
        title="Important alerts & notifications"
        figmaFrame="67:4882"
        onRefresh={() => void refetch()}
      />
      <QueryState
        isLoading={isLoading}
        isError={isError}
        error={error}
        isEmpty={!data?.notifications.length}
        onRetry={() => void refetch()}
      >
        <ul className="divide-y rounded-xl border border-[#dce3ec] bg-white">
          {data?.notifications.map((n, idx) => (
            <li key={`${n.title}-${idx}`} className="px-4 py-3 text-sm">
              <p className="font-medium text-[#172b45]">{n.title}</p>
              <p className="text-[#607086]">{n.message}</p>
            </li>
          ))}
        </ul>
      </QueryState>
    </div>
  );
}

function DashboardStatsShell({
  frame,
  title,
  query,
  emphasis,
}: {
  frame: string;
  title: string;
  query: ReturnType<typeof useDashboardStatistics>;
  emphasis: "students" | "faculty" | "departments";
}) {
  const stats = query.data?.statistics;
  const cards =
    emphasis === "students"
      ? [
          ["Total students", stats?.total_students],
          ["Active students", stats?.active_students],
          ["Programmes", stats?.programme_count],
        ]
      : emphasis === "faculty"
        ? [
            ["Faculty", stats?.faculty_count],
            ["Employees", stats?.employee_count],
            ["Departments", stats?.department_count],
          ]
        : [
            ["Departments", stats?.department_count],
            ["Programmes", stats?.programme_count],
            ["Students", stats?.total_students],
          ];

  return (
    <div data-figma-frame={frame}>
      <PageHeading title={title} figmaFrame={frame} onRefresh={() => void query.refetch()} />
      <QueryState
        isLoading={query.isLoading}
        isError={query.isError}
        error={query.error}
        onRetry={() => void query.refetch()}
      >
        <div className="grid gap-4 sm:grid-cols-3">
          {cards.map(([label, value]) => (
            <StatCard
              key={String(label)}
              label={String(label)}
              value={value ?? 0}
            />
          ))}
        </div>
      </QueryState>
    </div>
  );
}

function OperationalView({
  frame,
  title,
  query,
  section,
}: {
  frame: string;
  title: string;
  query: ReturnType<typeof useOperationalSummaries>;
  section?: "attendance" | "exams" | "finance";
}) {
  const d = query.data;
  return (
    <div data-figma-frame={frame}>
      <PageHeading title={title} figmaFrame={frame} onRefresh={() => void query.refetch()} />
      <QueryState
        isLoading={query.isLoading}
        isError={query.isError}
        error={query.error}
        onRetry={() => void query.refetch()}
      >
        <div className="grid gap-4 sm:grid-cols-3">
          {section === "attendance" || !section ? (
            <>
              <StatCard
                label="Sessions submitted"
                value={d?.attendance.sessions_submitted ?? 0}
              />
              <StatCard
                label="Pending submissions"
                value={d?.attendance.pending_submissions ?? 0}
              />
              <StatCard
                label="Corrections open"
                value={d?.attendance.correction_requests_open ?? 0}
              />
            </>
          ) : null}
          {section === "exams" ? (
            <>
              <StatCard label="Scheduled" value={d?.examinations.scheduled_exams ?? 0} />
              <StatCard
                label="Pending evaluations"
                value={d?.examinations.pending_evaluations ?? 0}
              />
              <StatCard
                label="Published results"
                value={d?.examinations.published_results ?? 0}
              />
            </>
          ) : null}
          {section === "finance" ? (
            <>
              <StatCard
                label="Collected"
                value={formatMoney(d?.finance.collected_amount ?? 0)}
              />
              <StatCard
                label="Outstanding"
                value={formatMoney(d?.finance.outstanding_amount ?? 0)}
              />
              <StatCard label="Open demands" value={d?.finance.open_demands ?? 0} />
            </>
          ) : null}
        </div>
      </QueryState>
    </div>
  );
}