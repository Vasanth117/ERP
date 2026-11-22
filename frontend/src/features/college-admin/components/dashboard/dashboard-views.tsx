"use client";

import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { CollegeAdminKpiGrid } from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState, StatCard } from "@/features/college-admin/components/ui/query-state";
import { PageHeading } from "@/features/college-admin/components/layout/page-heading";
import { CollegeOverviewDashboard } from "@/features/college-admin/components/dashboard/college-overview-dashboard";
import { InstitutionalOverviewDashboard } from "@/features/college-admin/components/dashboard/institutional-overview-dashboard";
import { AcademicPerformanceDashboard } from "@/features/college-admin/components/dashboard/academic-performance-dashboard";
import { AttendanceOverviewDashboard } from "@/features/college-admin/components/dashboard/attendance-overview-dashboard";
import { ExaminationOverviewDashboard } from "@/features/college-admin/components/dashboard/examination-overview-dashboard";
import { FinanceSummaryDashboard } from "@/features/college-admin/components/dashboard/finance-summary-dashboard";
import { PendingApprovalsDashboard } from "@/features/college-admin/components/dashboard/pending-approvals-dashboard";
import { RecentActivitiesDashboard } from "@/features/college-admin/components/dashboard/recent-activities-dashboard";
import { AlertsDashboard } from "@/features/college-admin/components/dashboard/alerts-dashboard";
import { DepartmentPerformanceDashboard } from "@/features/college-admin/components/dashboard/department-performance-dashboard";
import { FacultyStatisticsDashboard } from "@/features/college-admin/components/dashboard/faculty-statistics-dashboard";
import { StudentStatisticsDashboard } from "@/features/college-admin/components/dashboard/student-statistics-dashboard";
import {
  useDashboardOverview,
  useDashboardStatistics,
  useOperationalSummaries,
} from "@/features/college-admin/hooks/use-dashboard";

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function DashboardOverviewView() {
  return <CollegeOverviewDashboard />;
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
    <CollegeAdminKpiGrid columns={3}>
      <StatCard
        label="Attendance sessions"
        value={attendance?.sessions_submitted ?? 0}
        hint={`${attendance?.pending_submissions ?? 0} pending`}
        kpiKey="attendance_sessions"
        iconSlug="clipboard-check"
      />
      <StatCard
        label="Scheduled exams"
        value={exams?.scheduled_exams ?? 0}
        hint={`${exams?.pending_evaluations ?? 0} pending evaluations`}
        kpiKey="scheduled_exams"
        iconSlug="file-text"
      />
      <StatCard
        label="Fees collected"
        value={formatMoney(finance?.collected_amount ?? 0)}
        hint={`Outstanding ${formatMoney(finance?.outstanding_amount ?? 0)}`}
        kpiKey="fees_collected"
        iconSlug="wallet"
      />
      <StatCard
        label="Pending approvals"
        value={pending ?? 0}
        hint={`${support ?? 0} open support items`}
        kpiKey="pending_approvals"
        iconSlug="square-check"
      />
      <StatCard
        label="Library circulation"
        value={library?.active_circulation ?? 0}
        hint={`${library?.catalog_items ?? 0} catalogue items`}
        kpiKey="library_circulation"
        iconSlug="library-big"
      />
      <StatCard
        label="Hostel allocations"
        value={library?.hostel_allocations ?? 0}
        hint={`${library?.pending_hostel_applications ?? 0} applications`}
        kpiKey="hostel_allocations"
        iconSlug="hotel"
      />
    </CollegeAdminKpiGrid>
  );
}

export function InstitutionalOverviewDashboardView() {
  return <InstitutionalOverviewDashboard />;
}

export function StudentStatisticsView() {
  return <StudentStatisticsDashboard />;
}

export function FacultyStatisticsView() {
  return <FacultyStatisticsDashboard />;
}

export function DepartmentPerformanceView() {
  return <DepartmentPerformanceDashboard />;
}

export function AcademicAnalyticsView() {
  return <AcademicPerformanceDashboard />;
}

export function AttendanceOverviewView() {
  return <AttendanceOverviewDashboard />;
}

export function ExaminationOverviewView() {
  return <ExaminationOverviewDashboard />;
}

export function FinanceSummaryView() {
  return <FinanceSummaryDashboard />;
}

export function PendingApprovalsView() {
  return <PendingApprovalsDashboard />;
}

export function RecentActivitiesView() {
  return <RecentActivitiesDashboard />;
}

export function AlertsDashboardView() {
  return <AlertsDashboard />;
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
      <PageHeading title={title} figmaFrame={frame} />
      <QueryState
        isLoading={query.isLoading}
        isError={query.isError}
        error={query.error}
        onRetry={() => void query.refetch()}
      >
        <CollegeAdminKpiGrid columns={3}>
          {cards.map(([label, value]) => (
            <StatCard
              key={String(label)}
              label={String(label)}
              value={value ?? 0}
              kpiKey={String(label)}
            />
          ))}
        </CollegeAdminKpiGrid>
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
      <PageHeading title={title} figmaFrame={frame} />
      <QueryState
        isLoading={query.isLoading}
        isError={query.isError}
        error={query.error}
        onRetry={() => void query.refetch()}
      >
        <CollegeAdminKpiGrid columns={3}>
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
              <StatCard
                label="Open demands"
                value={d?.finance.open_demands ?? 0}
                kpiKey="open_demands"
              />
            </>
          ) : null}
        </CollegeAdminKpiGrid>
      </QueryState>
    </div>
  );
}