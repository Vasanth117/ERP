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
  TimetableDailyPage,
  TimetableLaboratoryPage,
  TimetableMonthlyPage,
  TimetableOverviewPage,
  TimetableSemester,
  TimetableSessionDetail,
  TimetableWeek,
  TimetableWeeklyPage,
} from "@/features/student/types/timetable";

const BASE = "/students";

export function fetchTimetableOverview(anchorDate?: string) {
  return apiRequest<TimetableOverviewPage>(
    `${BASE}/me/timetable/overview${optionalQuery({ anchor_date: anchorDate })}`,
  );
}

export type TimetableViewPageParams = {
  anchorDate?: string;
  courseCode?: string;
  slotId?: string;
};

export function fetchTimetableDailyPage(params: TimetableViewPageParams = {}) {
  return apiRequest<TimetableDailyPage>(
    `${BASE}/me/timetable/daily-page${optionalQuery({
      anchor_date: params.anchorDate,
      course_code: params.courseCode,
      slot_id: params.slotId,
    })}`,
  );
}

export function fetchTimetableWeeklyPage(params: Omit<TimetableViewPageParams, "slotId"> = {}) {
  return apiRequest<TimetableWeeklyPage>(
    `${BASE}/me/timetable/weekly-page${optionalQuery({
      anchor_date: params.anchorDate,
      course_code: params.courseCode,
    })}`,
  );
}

export function fetchTimetableMonthlyPage(anchorDate?: string) {
  return apiRequest<TimetableMonthlyPage>(
    `${BASE}/me/timetable/monthly-page${optionalQuery({ anchor_date: anchorDate })}`,
  );
}

export function fetchTimetableLaboratoryPage(params: TimetableViewPageParams = {}) {
  return apiRequest<TimetableLaboratoryPage>(
    `${BASE}/me/timetable/laboratory-page${optionalQuery({
      anchor_date: params.anchorDate,
      course_code: params.courseCode,
      slot_id: params.slotId,
    })}`,
  );
}

export function fetchTimetableSessionDetail(slotId: string, anchorDate?: string) {
  return apiRequest<TimetableSessionDetail>(
    `${BASE}/me/timetable/slots/${encodeURIComponent(slotId)}/session-detail${optionalQuery({
      anchor_date: anchorDate,
    })}`,
  );
}

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