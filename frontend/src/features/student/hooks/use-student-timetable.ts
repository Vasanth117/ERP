"use client";

import { useQuery } from "@tanstack/react-query";

import {
  fetchAcademicCalendar,
  fetchCalendarDeadlines,
  fetchCancelledSessions,
  fetchDailyTimetable,
  fetchExaminationSchedule,
  fetchSemesterTimetable,
  fetchTimetableDailyPage,
  fetchTimetableLaboratoryPage,
  fetchTimetableMonthlyPage,
  fetchTimetableSessionDetail,
  fetchTimetableWeeklyPage,
  fetchTimetableChanges,
  fetchTimetableNotifications,
  fetchTimetableOverview,
  fetchWeeklyTimetable,
  type TimetableViewPageParams,
} from "@/features/student/api/timetable";
import { studentQueryKeys } from "@/features/student/query-keys";

export function useTimetableOverview(anchorDate?: string) {
  return useQuery({
    queryKey: studentQueryKeys.timetableOverview(anchorDate),
    queryFn: () => fetchTimetableOverview(anchorDate),
    retry: false,
  });
}

export type TimetablePageQueryOptions = { enabled?: boolean };

export function useTimetableDailyPage(
  params: TimetableViewPageParams & TimetablePageQueryOptions = {},
) {
  const { enabled = true, ...fetchParams } = params;
  return useQuery({
    queryKey: studentQueryKeys.timetableDailyPage({
      date: fetchParams.anchorDate,
      course: fetchParams.courseCode,
      slot: fetchParams.slotId,
    }),
    queryFn: () => fetchTimetableDailyPage(fetchParams),
    enabled,
  });
}

export function useTimetableWeeklyPage(
  params: Omit<TimetableViewPageParams, "slotId"> & TimetablePageQueryOptions = {},
) {
  const { enabled = true, ...fetchParams } = params;
  return useQuery({
    queryKey: studentQueryKeys.timetableWeeklyPage({
      date: fetchParams.anchorDate,
      course: fetchParams.courseCode,
    }),
    queryFn: () => fetchTimetableWeeklyPage(fetchParams),
    enabled,
  });
}

export function useTimetableMonthlyPage(anchorDate?: string, options: TimetablePageQueryOptions = {}) {
  return useQuery({
    queryKey: studentQueryKeys.timetableMonthlyPage(anchorDate),
    queryFn: () => fetchTimetableMonthlyPage(anchorDate),
    enabled: options.enabled ?? true,
  });
}

export function useTimetableLaboratoryPage(
  params: TimetableViewPageParams & TimetablePageQueryOptions = {},
) {
  const { enabled = true, ...fetchParams } = params;
  return useQuery({
    queryKey: studentQueryKeys.timetableLaboratoryPage({
      date: fetchParams.anchorDate,
      course: fetchParams.courseCode,
      slot: fetchParams.slotId,
    }),
    queryFn: () => fetchTimetableLaboratoryPage(fetchParams),
    enabled,
  });
}

export function useTimetableSessionDetail(slotId: string | null, anchorDate?: string) {
  return useQuery({
    queryKey: studentQueryKeys.timetableSessionDetail(slotId ?? "", anchorDate),
    queryFn: () => fetchTimetableSessionDetail(slotId!, anchorDate),
    enabled: Boolean(slotId),
  });
}

export function useDailyTimetable(anchorDate?: string, courseCode?: string) {
  return useQuery({
    queryKey: studentQueryKeys.timetableDaily(anchorDate, courseCode),
    queryFn: () => fetchDailyTimetable(anchorDate, courseCode),
  });
}

export function useWeeklyTimetable(anchorDate?: string, courseCode?: string) {
  return useQuery({
    queryKey: studentQueryKeys.timetableWeekly(anchorDate, courseCode),
    queryFn: () => fetchWeeklyTimetable(anchorDate, courseCode),
  });
}

export function useSemesterTimetable(courseCode?: string) {
  return useQuery({
    queryKey: studentQueryKeys.timetableSemester(courseCode),
    queryFn: () => fetchSemesterTimetable(courseCode),
  });
}

export function useAcademicCalendar() {
  return useQuery({
    queryKey: studentQueryKeys.academicCalendar(),
    queryFn: () => fetchAcademicCalendar(),
  });
}

export function useCalendarDeadlines(limit = 50, offset = 0) {
  return useQuery({
    queryKey: studentQueryKeys.calendarDeadlines(limit, offset),
    queryFn: () => fetchCalendarDeadlines(limit, offset),
  });
}

export function useExaminationSchedule() {
  return useQuery({
    queryKey: studentQueryKeys.examinationSchedule(),
    queryFn: fetchExaminationSchedule,
  });
}

export function useTimetableChanges() {
  return useQuery({
    queryKey: studentQueryKeys.timetableChanges(),
    queryFn: fetchTimetableChanges,
  });
}

export function useTimetableNotifications() {
  return useQuery({
    queryKey: studentQueryKeys.timetableNotifications(),
    queryFn: fetchTimetableNotifications,
  });
}

export function useCancelledSessions() {
  return useQuery({
    queryKey: studentQueryKeys.cancelledSessions(),
    queryFn: fetchCancelledSessions,
  });
}