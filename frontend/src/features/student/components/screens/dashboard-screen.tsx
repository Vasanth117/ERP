"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import {
  PageHeading,
  QueryState,
  SectionPanel,
  StatCard,
  formatDate,
  formatDateTime,
  formatTime,
} from "@/features/student/components/ui/student-screen-ui";
import {
  useDashboardActivities,
  useStudentDashboard,
  useStudentDashboardStats,
} from "@/features/student/hooks/use-student-dashboard";

export function StudentDashboardScreen() {
  const dashboard = useStudentDashboard();
  const stats = useStudentDashboardStats();
  const activities = useDashboardActivities(15, 0);

  return (
    <div>
      <PageHeading
        title="Student Dashboard"
        description="Welcome back — live summary from GET /students/me/dashboard."
        figmaPage="ST 01"
      />

      <QueryState
        isLoading={dashboard.isLoading}
        isError={dashboard.isError}
        error={dashboard.error}
        onRetry={() => void dashboard.refetch()}
      >
        {dashboard.data ? (
          <div className="space-y-6">
            <section className="grid gap-4 rounded-xl border border-[#e8ecf2] bg-white p-5 lg:grid-cols-[1fr_280px]">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-[#9ca3af]">
                  {dashboard.data.academic_term.academic_year_label ?? "Academic year"} ·{" "}
                  {dashboard.data.academic_term.semester_label ?? "Semester"}
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-[#111827]">
                  Hello, {dashboard.data.profile.full_name}
                </h2>
                <p className="mt-2 text-sm text-[#6b7280]">
                  {dashboard.data.profile.programme_name ?? dashboard.data.profile.programme_code ?? "Programme"}
                  {dashboard.data.profile.section_code
                    ? ` · Section ${dashboard.data.profile.section_code}`
                    : ""}
                </p>
                <p className="mt-1 text-xs text-[#9ca3af]">
                  Roll {dashboard.data.profile.roll_number ?? "—"} · ID{" "}
                  {dashboard.data.profile.student_id ?? "—"}
                </p>
              </div>
              <RegistrationCard fees={dashboard.data.fees} />
            </section>

            <QueryState
              isLoading={stats.isLoading}
              isError={stats.isError}
              error={stats.error}
              onRetry={() => void stats.refetch()}
            >
              {stats.data ? (
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                  <StatCard
                    label="Enrolled courses"
                    value={stats.data.enrolled_course_count}
                    hint="This term"
                  />
                  <StatCard
                    label="Pending assignments"
                    value={stats.data.pending_assignment_count}
                  />
                  <StatCard
                    label="Attendance"
                    value={
                      stats.data.attendance_overall_percentage != null
                        ? `${stats.data.attendance_overall_percentage.toFixed(1)}%`
                        : "—"
                    }
                  />
                  <StatCard
                    label="Unread notifications"
                    value={stats.data.unread_notification_count}
                  />
                </div>
              ) : null}
            </QueryState>

            <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
              <SectionPanel title="Today's timetable" actionHref="/student/curriculum" actionLabel="Curriculum">
                <TableShell
                  headers={["Time", "Course", "Room"]}
                  empty={dashboard.data.timetable_today.length === 0}
                  emptyMessage="No classes scheduled today."
                >
                  {dashboard.data.timetable_today.map((slot, i) => (
                    <tr key={`${slot.course_code}-${i}`} className="border-t border-[#f1f5f9]">
                      <td className="px-3 py-3 text-sm text-[#111827]">
                        {formatTime(slot.start_time)} – {formatTime(slot.end_time)}
                      </td>
                      <td className="px-3 py-3 text-sm text-[#111827]">
                        <span className="font-medium">{slot.course_code}</span>
                        <span className="mt-0.5 block text-xs text-[#6b7280]">{slot.course_name}</span>
                      </td>
                      <td className="px-3 py-3 text-sm text-[#607086]">{slot.room ?? "—"}</td>
                    </tr>
                  ))}
                </TableShell>
              </SectionPanel>

              <SectionPanel title="Pending assignments">
                <ul className="divide-y divide-[#f1f5f9]">
                  {dashboard.data.pending_assignments.length === 0 ? (
                    <li className="py-6 text-center text-sm text-[#9ca3af]">No pending assignments.</li>
                  ) : (
                    dashboard.data.pending_assignments.map((task) => (
                      <li key={task.reference_id ?? task.title} className="py-3 text-sm">
                        <p className="font-medium text-[#111827]">{task.title}</p>
                        {task.due_at ? (
                          <p className="text-xs text-[#9ca3af]">Due {formatDateTime(task.due_at)}</p>
                        ) : null}
                      </li>
                    ))
                  )}
                </ul>
              </SectionPanel>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <SectionPanel title="Upcoming examinations">
                <ul className="divide-y divide-[#f1f5f9]">
                  {dashboard.data.upcoming_examinations.length === 0 ? (
                    <li className="py-6 text-center text-sm text-[#9ca3af]">No upcoming exams.</li>
                  ) : (
                    dashboard.data.upcoming_examinations.map((exam) => (
                      <li key={exam.reference_id ?? exam.title} className="py-3 text-sm">
                        <p className="font-medium text-[#111827]">{exam.title}</p>
                        {exam.due_at ? (
                          <p className="text-xs text-[#9ca3af]">{formatDateTime(exam.due_at)}</p>
                        ) : null}
                      </li>
                    ))
                  )}
                </ul>
              </SectionPanel>

              <SectionPanel title="Notifications">
                <ul className="divide-y divide-[#f1f5f9]">
                  {dashboard.data.notifications.length === 0 ? (
                    <li className="py-6 text-center text-sm text-[#9ca3af]">No notifications.</li>
                  ) : (
                    dashboard.data.notifications.map((n) => (
                      <li key={n.id} className="py-3 text-sm">
                        <p className="font-medium text-[#111827]">{n.title}</p>
                        <p className="mt-0.5 text-xs text-[#6b7280] line-clamp-2">{n.body}</p>
                        <p className="mt-1 text-[10px] text-[#9ca3af]">{formatDateTime(n.created_at)}</p>
                      </li>
                    ))
                  )}
                </ul>
              </SectionPanel>
            </div>

            <SectionPanel title="Recent activity" actionHref="/student/profile/activity" actionLabel="View all">
              <QueryState
                isLoading={activities.isLoading}
                isError={activities.isError}
                error={activities.error}
                onRetry={() => void activities.refetch()}
                isEmpty={!activities.data?.items.length}
                emptyMessage="No recent activity."
              >
                {activities.data ? (
                  <ul className="divide-y divide-[#f1f5f9]">
                    {activities.data.items.map((row) => (
                      <li key={row.id} className="flex justify-between gap-4 py-3 text-sm">
                        <div>
                          <p className="font-medium text-[#111827]">{row.title}</p>
                          {row.description ? (
                            <p className="text-xs text-[#6b7280]">{row.description}</p>
                          ) : null}
                        </div>
                        <time className="shrink-0 text-xs text-[#9ca3af]">
                          {formatDateTime(row.created_at)}
                        </time>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </QueryState>
            </SectionPanel>

            {dashboard.data.quick_actions.length > 0 ? (
              <section className="flex flex-wrap gap-2">
                {dashboard.data.quick_actions.map((action) =>
                  action.href && action.enabled ? (
                    <Link
                      key={action.code}
                      href={action.href}
                      className="inline-flex h-9 items-center rounded-lg border border-[#dce3ec] bg-white px-4 text-sm font-medium text-[#245dd8] hover:bg-[#f8fafc]"
                    >
                      {action.label}
                    </Link>
                  ) : null,
                )}
              </section>
            ) : null}
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}

function RegistrationCard({
  fees,
}: {
  fees: { status: string; outstanding_amount: number | null; due_date: string | null };
}) {
  return (
    <aside className="rounded-lg border border-[#e8ecf2] bg-[#f8fafc] p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-[#9ca3af]">Fees</p>
      <p className="mt-2 text-lg font-semibold capitalize text-[#111827]">{fees.status}</p>
      {fees.outstanding_amount != null ? (
        <p className="mt-1 text-sm text-[#6b7280]">
          Outstanding: ₹{fees.outstanding_amount.toLocaleString()}
        </p>
      ) : null}
      {fees.due_date ? (
        <p className="mt-1 text-xs text-[#9ca3af]">Due {formatDate(fees.due_date)}</p>
      ) : null}
      <Link
        href="/student/registration"
        className="mt-3 inline-block text-sm font-medium text-[#245dd8] hover:underline"
      >
        Course registration →
      </Link>
    </aside>
  );
}

function TableShell({
  headers,
  children,
  empty,
  emptyMessage,
}: {
  headers: string[];
  children: ReactNode;
  empty: boolean;
  emptyMessage: string;
}) {
  if (empty) {
    return <p className="py-8 text-center text-sm text-[#9ca3af]">{emptyMessage}</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[420px] text-left">
        <thead>
          <tr className="bg-[#f8fafc] text-xs font-medium uppercase tracking-wide text-[#9ca3af]">
            {headers.map((h) => (
              <th key={h} className="px-3 py-2">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}