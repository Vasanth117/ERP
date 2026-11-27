"use client";

import { useState } from "react";

import {
  DetailRow,
  PageHeading,
  QueryState,
  SectionPanel,
  formatDateTime,
} from "@/features/student/components/ui/student-screen-ui";
import { screenBySlug } from "@/features/student/config/screens";
import {
  DateAnchorField,
  EventsList,
  TimetableSlotsTable,
} from "@/features/student/components/screens/shared-tables";
import { TimetableOverviewScreen } from "@/features/student/components/screens/timetable-overview-screen";
import {
  useAcademicCalendar,
  useCalendarDeadlines,
  useCancelledSessions,
  useDailyTimetable,
  useExaminationSchedule,
  useSemesterTimetable,
  useTimetableChanges,
  useTimetableNotifications,
  useWeeklyTimetable,
} from "@/features/student/hooks/use-student-timetable";

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export type TimetableSlug =
  | "timetable"
  | "daily-timetable"
  | "weekly-timetable"
  | "semester-timetable"
  | "academic-calendar"
  | "calendar-deadlines"
  | "examination-schedule"
  | "timetable-changes"
  | "timetable-notifications"
  | "cancelled-sessions";

export function TimetableScreen({ slug }: { slug: TimetableSlug }) {
  if (slug === "timetable") {
    return <TimetableOverviewScreen />;
  }
  const def = screenBySlug(slug);
  return (
    <div>
      <PageHeading title={def?.title ?? "Timetable"} description={def?.description} figmaPage="ST 05" />
      <TimetableBody slug={slug} />
    </div>
  );
}

function TimetableBody({ slug }: { slug: TimetableSlug }) {
  switch (slug) {
    case "daily-timetable":
      return <DailyTimetableView />;
    case "weekly-timetable":
      return <WeeklyTimetableView />;
    case "semester-timetable":
      return <SemesterTimetableView />;
    case "academic-calendar":
      return <CalendarView />;
    case "calendar-deadlines":
      return <DeadlinesView />;
    case "examination-schedule":
      return <ExamScheduleView />;
    case "timetable-changes":
      return <ChangesView />;
    case "timetable-notifications":
      return <NotificationsView />;
    case "cancelled-sessions":
      return <CancelledView />;
    default:
      return null;
  }
}

function DailyTimetableView() {
  const [date, setDate] = useState(todayIso());
  const daily = useDailyTimetable(date);
  return (
    <SectionPanel title="Daily timetable">
      <DateAnchorField value={date} onChange={setDate} />
      <QueryState isLoading={daily.isLoading} isError={daily.isError} error={daily.error} onRetry={() => void daily.refetch()}>
        {daily.data ? <TimetableSlotsTable slots={daily.data.slots} /> : null}
      </QueryState>
    </SectionPanel>
  );
}

function WeeklyTimetableView() {
  const [date, setDate] = useState(todayIso());
  const weekly = useWeeklyTimetable(date);
  return (
    <SectionPanel title="Weekly timetable">
      <DateAnchorField value={date} onChange={setDate} label="Week containing" />
      <QueryState isLoading={weekly.isLoading} isError={weekly.isError} error={weekly.error} onRetry={() => void weekly.refetch()}>
        {weekly.data ? (
          <div className="space-y-6">
            {weekly.data.days.map((day) => (
              <div key={day.anchor_date}>
                <p className="mb-2 text-xs font-semibold uppercase text-[#9ca3af]">{day.anchor_date}</p>
                <TimetableSlotsTable slots={day.slots} />
              </div>
            ))}
          </div>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function SemesterTimetableView() {
  const sem = useSemesterTimetable();
  return (
    <SectionPanel title="Semester timetable">
      <QueryState isLoading={sem.isLoading} isError={sem.isError} error={sem.error} onRetry={() => void sem.refetch()}>
        {sem.data ? (
          <>
            <DetailRow label="Term" value={`${sem.data.academic_year_label} · ${sem.data.semester_label}`} />
            <div className="mt-4">
              <h4 className="mb-2 text-sm font-semibold">Active slots</h4>
              <TimetableSlotsTable slots={sem.data.slots} />
            </div>
          </>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function CalendarView() {
  const calendar = useAcademicCalendar();
  return (
    <SectionPanel title="Academic calendar">
      <QueryState isLoading={calendar.isLoading} isError={calendar.isError} error={calendar.error} onRetry={() => void calendar.refetch()} isEmpty={!calendar.data?.length}>
        {calendar.data ? <EventsList items={calendar.data} /> : null}
      </QueryState>
    </SectionPanel>
  );
}

function DeadlinesView() {
  const deadlines = useCalendarDeadlines(50, 0);
  return (
    <SectionPanel title="Deadlines">
      <QueryState isLoading={deadlines.isLoading} isError={deadlines.isError} error={deadlines.error} onRetry={() => void deadlines.refetch()} isEmpty={!deadlines.data?.items.length}>
        {deadlines.data ? <EventsList items={deadlines.data.items} /> : null}
      </QueryState>
    </SectionPanel>
  );
}

function ExamScheduleView() {
  const exams = useExaminationSchedule();
  return (
    <SectionPanel title="Examination schedule">
      <QueryState isLoading={exams.isLoading} isError={exams.isError} error={exams.error} onRetry={() => void exams.refetch()} isEmpty={!exams.data?.length}>
        {exams.data ? (
          <ul className="divide-y divide-[#f1f5f9] text-sm">
            {exams.data.map((e) => (
              <li key={e.id} className="py-3">
                <p className="font-medium">{e.title}</p>
                <p className="text-xs text-[#6b7280]">
                  {e.course_code} · {e.exam_type} · {formatDateTime(e.scheduled_at)}
                </p>
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function ChangesView() {
  const changes = useTimetableChanges();
  return (
    <SectionPanel title="Timetable changes">
      <QueryState isLoading={changes.isLoading} isError={changes.isError} error={changes.error} onRetry={() => void changes.refetch()} isEmpty={!changes.data?.length}>
        {changes.data ? (
          <ul className="divide-y divide-[#f1f5f9] text-sm">
            {changes.data.map((c) => (
              <li key={c.id} className="py-3">
                <p className="font-medium capitalize">{c.change_type.replace(/_/g, " ")}</p>
                <p className="text-[#6b7280]">{c.summary}</p>
                <p className="text-xs text-[#9ca3af]">{formatDateTime(c.effective_at)}</p>
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function NotificationsView() {
  const notes = useTimetableNotifications();
  return (
    <SectionPanel title="Timetable notifications">
      <QueryState isLoading={notes.isLoading} isError={notes.isError} error={notes.error} onRetry={() => void notes.refetch()} isEmpty={!notes.data?.length}>
        {notes.data ? (
          <ul className="divide-y divide-[#f1f5f9] text-sm">
            {notes.data.map((n) => (
              <li key={n.id} className="py-3">
                <p className="font-medium">{n.title}</p>
                <p className="text-[#6b7280]">{n.body}</p>
                <p className="text-xs text-[#9ca3af]">{formatDateTime(n.created_at)}</p>
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function CancelledView() {
  const sessions = useCancelledSessions();
  return (
    <SectionPanel title="Cancelled / rescheduled sessions">
      <QueryState isLoading={sessions.isLoading} isError={sessions.isError} error={sessions.error} onRetry={() => void sessions.refetch()} isEmpty={!sessions.data?.length}>
        {sessions.data ? (
          <ul className="divide-y divide-[#f1f5f9] text-sm">
            {sessions.data.map((s) => (
              <li key={s.id} className="py-3">
                <p className="font-medium">
                  {s.course_code} · {s.section}
                </p>
                <p className="text-xs text-[#6b7280]">
                  {formatDateTime(s.scheduled_start)} – {formatDateTime(s.scheduled_end)} · {s.status}
                </p>
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}