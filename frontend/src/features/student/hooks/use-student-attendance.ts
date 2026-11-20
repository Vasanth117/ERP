"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchAttendanceEligibility,
  fetchAttendanceExport,
  fetchAttendanceHistory,
  fetchAttendanceShortages,
  fetchAttendanceSummary,
  fetchDailyAttendance,
  fetchDiscrepancyRequests,
  fetchSubjectAttendance,
  submitDiscrepancyRequest,
} from "@/features/student/api/attendance";
import { studentQueryKeys } from "@/features/student/query-keys";
import type { DiscrepancyRequestCreate } from "@/features/student/types/attendance";

export function useAttendanceSummary() {
  return useQuery({
    queryKey: studentQueryKeys.attendanceSummary(),
    queryFn: fetchAttendanceSummary,
  });
}

export function useSubjectAttendance() {
  return useQuery({
    queryKey: studentQueryKeys.attendanceSubjects(),
    queryFn: fetchSubjectAttendance,
  });
}

export function useDailyAttendance(sessionDate: string) {
  return useQuery({
    queryKey: studentQueryKeys.attendanceDaily(sessionDate),
    queryFn: () => fetchDailyAttendance(sessionDate),
    enabled: Boolean(sessionDate),
  });
}

export function useAttendanceHistory(limit = 50, offset = 0) {
  return useQuery({
    queryKey: studentQueryKeys.attendanceHistory(limit, offset),
    queryFn: () => fetchAttendanceHistory(limit, offset),
  });
}

export function useAttendanceShortages() {
  return useQuery({
    queryKey: studentQueryKeys.attendanceShortages(),
    queryFn: fetchAttendanceShortages,
  });
}

export function useAttendanceEligibility() {
  return useQuery({
    queryKey: studentQueryKeys.attendanceEligibility(),
    queryFn: fetchAttendanceEligibility,
  });
}

export function useAttendanceExport() {
  return useQuery({
    queryKey: studentQueryKeys.attendanceExport(),
    queryFn: fetchAttendanceExport,
    enabled: false,
  });
}

export function useDiscrepancyRequests(limit = 50, offset = 0) {
  return useQuery({
    queryKey: studentQueryKeys.discrepancyRequests(limit, offset),
    queryFn: () => fetchDiscrepancyRequests(limit, offset),
  });
}

export function useSubmitDiscrepancyRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: DiscrepancyRequestCreate) => submitDiscrepancyRequest(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: studentQueryKeys.discrepancyRequests(50, 0) });
    },
  });
}