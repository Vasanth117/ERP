"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useMemo } from "react";

import type { ErpIconName } from "@/components/icons/erp/names";
import {
  CollegeAdminDashboardKpiCard,
  CollegeAdminKpiGrid,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import {
  StNoticeBanner,
  StNotificationRow,
  type StNotificationBadgeTone,
} from "@/features/student/components/ui/student-dashboard-ui";
import {
  courseDisplayName,
  formatBacklogKpi,
  formatCgpaKpi,
  formatStudentFeesKpi,
} from "@/features/student/lib/student-kpi-format";
import {
  QueryState,
  SectionPanel,
  formatDateTime,
  formatTime,
} from "@/features/student/components/ui/student-screen-ui";
import { screenBySlug } from "@/features/student/config/screens";
import {
  useStudentBacklogSummary,
  useStudentCgpa,
  useStudentDashboard,
} from "@/features/student/hooks/use-student-dashboard";
import { useAttendanceShortages } from "@/features/student/hooks/use-student-attendance";
import { useDailyTimetable } from "@/features/student/hooks/use-student-timetable";
import type { QuickAction } from "@/features/student/types/dashboard";
import type { TimetableSlot } from "@/features/student/types/timetable";

const screen = screenBySlug("dashboard");

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function frontendQuickActionHref(action: QuickAction): string | null {
  if (!action.enabled) return null;
  const routes: Record<string, string> = {
    view_timetable: "/student/timetable/schedule",
    submit_assignment: "/student/assessments",
    fee_status: "/under-construction?module=student-fees",
    edit_profile: "/student/profile",
  };
  return routes[action.code] ?? (action.href?.startsWith("/student") ? action.href : null);
}

function notificationPresentation(category: string): {
  icon: ErpIconName;
  badgeLabel: string;
  tone: StNotificationBadgeTone;
} {
  const normalized = category.toLowerCase();
  if (normalized === "examination") {
    return { icon: "id-card", badgeLabel: "Exam", tone: "exam" };
  }
  if (normalized === "finance") {
    return { icon: "indian-rupee", badgeLabel: "Fees", tone: "fees" };
  }
  if (normalized === "academic") {
    return { icon: "book-open-check", badgeLabel: "Academic", tone: "info" };
  }
  return { icon: "bell", badgeLabel: "General", tone: "info" };
}

export function StudentDashboardScreen() {
  const pathname = usePathname() ?? "/student/dashboard";
  const studentLoginHref = `/login?portal=student-performance&next=${encodeURIComponent(pathname)}`;

  const dashboard = useStudentDashboard();
  const cgpa = useStudentCgpa();
  const backlog = useStudentBacklogSummary();
  const dailyTimetable = useDailyTimetable(todayIso());
  const shortages = useAttendanceShortages();

  const slotDetails = useMemo(() => {
    const map = new Map<string, TimetableSlot>();
    for (const slot of dailyTimetable.data?.slots ?? []) {
      map.set(`${slot.course_code}|${slot.start_time}`, slot);
    }
    return map;
  }, [dailyTimetable.data?.slots]);

  const payFeesHref = useMemo(() => {
    const action = dashboard.data?.quick_actions.find((a) => a.code === "fee_status");
    return action ? frontendQuickActionHref(action) : null;
  }, [dashboard.data?.quick_actions]);

  const timetableHref = useMemo(() => {
    const action = dashboard.data?.quick_actions.find((a) => a.code === "view_timetable");
    return action ? frontendQuickActionHref(action) ?? "/student/timetable/schedule" : "/student/timetable/schedule";
  }, [dashboard.data?.quick_actions]);

  return (
    <div className="space-y-5" data-figma-node="164:236">
      <QueryState
        isLoading={dashboard.isLoading}
        isError={dashboard.isError}
        error={dashboard.error}
        onRetry={() => void dashboard.refetch()}
        loginHref={studentLoginHref}
        loginLabel="Student sign in"
        unauthorizedMessage="Your session is missing or expired. Sign in with the student demo account (Student ID login), not the College Admin email."
      >
        {dashboard.data ? (
          <DashboardBody
            dashboard={dashboard.data}
            cgpaLoading={cgpa.isLoading}
            cgpa={cgpa.data}
            backlogLoading={backlog.isLoading}
            backlog={backlog.data}
            shortages={shortages.data}
            slotDetails={slotDetails}
            timetableHref={timetableHref}
            payFeesHref={payFeesHref}
            dailyLoading={dailyTimetable.isLoading}
          />
        ) : null}
      </QueryState>
    </div>
  );
}

function DashboardBody({
  dashboard,
  cgpaLoading,
  cgpa,
  backlogLoading,
  backlog,
  shortages,
  slotDetails,
  timetableHref,
  payFeesHref,
  dailyLoading,
}: {
  dashboard: NonNullable<ReturnType<typeof useStudentDashboard>["data"]>;
  cgpaLoading: boolean;
  cgpa: ReturnType<typeof useStudentCgpa>["data"];
  backlogLoading: boolean;
  backlog: ReturnType<typeof useStudentBacklogSummary>["data"];
  shortages: ReturnType<typeof useAttendanceShortages>["data"];
  slotDetails: Map<string, TimetableSlot>;
  timetableHref: string;
  payFeesHref: string | null;
  dailyLoading: boolean;
}) {
  const profile = dashboard.profile;
  const term = dashboard.academic_term;
  const attendance = dashboard.attendance;
  const fees = dashboard.fees;

  const nameSources = [
    ...dashboard.enrolled_courses.map((c) => ({
      course_code: c.course_code,
      course_name: c.course_name,
    })),
    ...dashboard.timetable_today.map((c) => ({
      course_code: c.course_code,
      course_name: c.course_name,
    })),
  ];

  const primaryShortage = shortages?.[0];

  const attendanceValue =
    attendance.overall_percentage != null
      ? `${attendance.overall_percentage.toFixed(1)}%`
      : "—";

  const attendanceHint =
    attendance.min_required != null && attendance.overall_percentage != null
      ? attendance.overall_percentage >= attendance.min_required
        ? `Above ${attendance.min_required}% requirement`
        : `Below ${attendance.min_required}% requirement`
      : attendance.overall_percentage != null
        ? "Overall this term"
        : "Attendance not available yet";

  const attendanceTone =
    attendance.min_required != null &&
    attendance.overall_percentage != null &&
    attendance.overall_percentage < attendance.min_required
      ? "warning"
      : "success";

  const cgpaKpi = formatCgpaKpi(cgpaLoading ? null : cgpa?.cgpa, cgpa?.credits_earned);
  const cgpaValue = cgpaLoading ? "…" : cgpaKpi.value;
  const cgpaHint = cgpaKpi.hint;

  const backlogKpi = formatBacklogKpi(
    backlogLoading ? undefined : backlog?.pending_count,
    backlog?.cleared_count,
    backlog?.registered_count,
  );
  const backlogValue = backlogLoading ? "…" : backlogKpi.value;
  const backlogHint = backlogKpi.hint;

  const feesKpi = formatStudentFeesKpi(fees);
  const feesValue = feesKpi.value;
  const feesHint = feesKpi.hint;
  const feesTone = feesKpi.tone;

  return (
    <>
      <header className="flex flex-wrap items-start justify-between gap-4" data-figma-node="164:237">
        <div className="min-w-0">
          <h1 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {screen?.title ?? "Student dashboard"}
          </h1>
          <p className="mt-1 text-[14px] leading-relaxed text-[#6b7280]">
            Welcome back
            {profile?.full_name ? (
              <>
                , <span className="font-medium text-[#374151]">{profile.full_name}</span>
              </>
            ) : null}
            {term?.academic_year_label || term?.semester_label ? (
              <span>
                {" "}
                · {[term.academic_year_label, term.semester_label].filter(Boolean).join(" · ")}
              </span>
            ) : null}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Link
            href={timetableHref}
            className="inline-flex h-9 items-center rounded-md border border-[#e5e7eb] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            Timetable
          </Link>
          {payFeesHref ? (
            <Link
              href={payFeesHref}
              className="inline-flex h-9 items-center rounded-md border border-[#245dd8] bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
            >
              Pay fees
            </Link>
          ) : null}
        </div>
      </header>

      <CollegeAdminKpiGrid>
        <CollegeAdminDashboardKpiCard
          label="Attendance"
          value={attendanceValue}
          hint={attendanceHint}
          hintTone={attendanceTone === "warning" ? "warning" : "success"}
          kpiKey="attendance"
          index={0}
          iconSlug="clipboard-check"
        />
        <CollegeAdminDashboardKpiCard
          label="CGPA"
          value={cgpaValue}
          hint={cgpaHint}
          hintTone="info"
          kpiKey="cgpa"
          index={1}
          iconSlug="graduation-cap"
        />
        <CollegeAdminDashboardKpiCard
          label="Backlogs"
          value={backlogValue}
          hint={backlogHint}
          hintTone={
            Number(backlogValue) > 0 ? "warning" : "success"
          }
          kpiKey="backlogs"
          index={2}
          iconSlug="book-open-check"
        />
        <CollegeAdminDashboardKpiCard
          label="Fees due"
          value={feesValue}
          hint={feesHint}
          hintTone={feesTone === "warning" ? "warning" : "muted"}
          kpiKey="fees"
          index={3}
          iconSlug="indian-rupee"
        />
      </CollegeAdminKpiGrid>

      {primaryShortage && primaryShortage.percentage != null ? (
        <StNoticeBanner
          title={`Attendance below ${primaryShortage.min_required}% in ${courseDisplayName(primaryShortage.course_code, nameSources)}`}
          description={
            primaryShortage.sessions_remaining_to_clear != null
              ? `You are at ${Math.round(primaryShortage.percentage)}%. Attend the next ${primaryShortage.sessions_remaining_to_clear} classes to reach the required ${primaryShortage.min_required}%.`
              : `You are at ${Math.round(primaryShortage.percentage)}%. Minimum required is ${primaryShortage.min_required}%.`
          }
          href="/student/attendance/shortages"
          linkLabel="View shortage"
        />
      ) : null}

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <SectionPanel
            title="Today's classes"
            actionHref="/student/timetable/schedule"
            actionLabel="Full timetable →"
          >
            <TodayClassesTable
              slots={dashboard.timetable_today}
              slotDetails={slotDetails}
              loading={dailyLoading}
            />
            <p className="mt-3 border-t border-[#f1f5f9] pt-3 text-[11px] text-[#9ca3af]">
              Times and rooms from your live daily timetable.
            </p>
          </SectionPanel>
        </div>

        <SectionPanel
          title="Latest notifications"
          actionHref="/student/profile/activity"
          actionLabel="View all →"
        >
          <ul className="py-1">
            {dashboard.notifications.length === 0 ? (
              <li className="py-8 text-center text-[13px] text-[#607086]">No notifications yet.</li>
            ) : (
              dashboard.notifications.slice(0, 5).map((item) => {
                const presentation = notificationPresentation(item.category);
                return (
                  <StNotificationRow
                    key={item.id}
                    icon={presentation.icon}
                    title={item.title}
                    meta={formatDateTime(item.created_at)}
                    badgeLabel={presentation.badgeLabel}
                    badgeTone={presentation.tone}
                  />
                );
              })
            )}
          </ul>
        </SectionPanel>
      </div>

      <p className="text-[11px] text-[#8a98aa]">
        {screen?.description ??
          "Overview data is loaded from your student account for the active term."}
      </p>
    </>
  );
}

function TodayClassesTable({
  slots,
  slotDetails,
  loading,
}: {
  slots: NonNullable<ReturnType<typeof useStudentDashboard>["data"]>["timetable_today"];
  slotDetails: Map<string, TimetableSlot>;
  loading: boolean;
}) {
  if (!slots.length) {
    return (
      <p className="px-5 py-10 text-center text-[13px] text-[#607086]">
        {loading ? "Loading timetable…" : "No classes scheduled today."}
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[520px] text-left text-[13px]">
        <thead>
          <tr className="border-b border-[#dce3ec] text-[11px] font-semibold uppercase tracking-wide text-[#8a98aa]">
            <th className="px-5 py-2.5">Time</th>
            <th className="px-5 py-2.5">Subject</th>
            <th className="px-5 py-2.5">Type</th>
            <th className="px-5 py-2.5">Room</th>
            <th className="px-5 py-2.5">Faculty</th>
          </tr>
        </thead>
        <tbody>
          {slots.map((slot, index) => {
            const detail = slotDetails.get(`${slot.course_code}|${slot.start_time}`);
            const faculty =
              detail?.faculty?.map((member) => member.display_name).filter(Boolean).join(", ") ||
              "—";
            const sessionType = detail?.session_type
              ? detail.session_type.replaceAll("_", " ")
              : "—";

            return (
              <tr key={`${slot.course_code}-${slot.start_time}-${index}`} className="border-b border-[#eef1f5]">
                <td className="whitespace-nowrap px-5 py-3 text-[#172b45]">
                  {formatTime(slot.start_time)} – {formatTime(slot.end_time)}
                </td>
                <td className="px-5 py-3 text-[#172b45]">
                  <span className="font-medium">{slot.course_code}</span>
                  <span className="mt-0.5 block text-[11px] text-[#607086]">{slot.course_name}</span>
                </td>
                <td className="px-5 py-3 capitalize text-[#607086]">{sessionType}</td>
                <td className="px-5 py-3 text-[#607086]">{slot.room ?? detail?.room ?? "—"}</td>
                <td className="px-5 py-3 text-[#607086]">{faculty}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}