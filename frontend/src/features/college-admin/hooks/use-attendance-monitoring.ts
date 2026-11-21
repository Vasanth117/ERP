"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchAttendanceMonitoringPage,
  notifyFacultyMissingAttendance,
} from "@/features/college-admin/api/attendance-monitoring";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { AttendanceMonitoringQuery } from "@/features/college-admin/types/attendance-monitoring";

export function useAttendanceMonitoringPage(params?: AttendanceMonitoringQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.attendanceMonitoring(params),
    queryFn: () => fetchAttendanceMonitoringPage(params),
  });
}

export function useNotifyFacultyMissingAttendance(params?: AttendanceMonitoringQuery) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: notifyFacultyMissingAttendance,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.attendanceMonitoring(params) });
    },
  });
}