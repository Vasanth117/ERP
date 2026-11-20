import { apiRequest } from "@/lib/api/client";

import { optionalQuery } from "@/features/student/api/query-build";
import { pageQuery } from "@/features/student/api/pagination";
import type { ApiPage } from "@/features/student/types/common";
import type {
  CalendarEvent,
  ClassSession,
  ExaminationSchedule,
  TimetableChange,
  TimetableDay,
  TimetableNotification,
  TimetableSemester,
  TimetableWeek,
} from "@/features/student/types/timetable";

const BASE = "/students";

export function fetchDailyTimetable(anchorDate?: string, courseCode?: string) {
  return apiRequest<TimetableDay>(
    `${BASE}/me/timetable/daily${optionalQuery({ anchor_date: anchorDate, course_code: courseCode })}`,
  );
}

export function fetchWeeklyTimetable(anchorDate?: string, courseCode?: string) {
  return apiRequest<TimetableWeek>(
    `${BASE}/me/timetable/weekly${optionalQuery({ anchor_date: anchorDate, course_code: courseCode })}`,
  );
}

export function fetchSemesterTimetable(courseCode?: string) {
  return apiRequest<TimetableSemester>(
    `${BASE}/me/timetable/semester${optionalQuery({ course_code: courseCode })}`,
  );
}

export function fetchAcademicCalendar(limit = 50) {
  return apiRequest<CalendarEvent[]>(`${BASE}/me/timetable/calendar?limit=${limit}`);
}

export function fetchCalendarDeadlines(limit = 50, offset = 0) {
  return apiRequest<ApiPage<CalendarEvent>>(
    `${BASE}/me/timetable/calendar/deadlines?${pageQuery(limit, offset)}`,
  );
}

export function fetchExaminationSchedule() {
  return apiRequest<ExaminationSchedule[]>(`${BASE}/me/timetable/examinations`);
}

export function fetchTimetableChanges() {
  return apiRequest<TimetableChange[]>(`${BASE}/me/timetable/changes`);
}

export function fetchTimetableNotifications() {
  return apiRequest<TimetableNotification[]>(`${BASE}/me/timetable/notifications`);
}

export function fetchCancelledSessions() {
  return apiRequest<ClassSession[]>(`${BASE}/me/timetable/sessions/cancelled-rescheduled`);
}