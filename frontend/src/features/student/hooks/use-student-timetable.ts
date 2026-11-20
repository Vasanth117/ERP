"use client";

import { useQuery } from "@tanstack/react-query";

import {
  fetchAcademicCalendar,
  fetchCalendarDeadlines,
  fetchCancelledSessions,
  fetchDailyTimetable,
  fetchExaminationSchedule,
  fetchSemesterTimetable,
  fetchTimetableChanges,
  fetchTimetableNotifications,
  fetchWeeklyTimetable,
} from "@/features/student/api/timetable";
import { studentQueryKeys } from "@/features/student/query-keys";

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