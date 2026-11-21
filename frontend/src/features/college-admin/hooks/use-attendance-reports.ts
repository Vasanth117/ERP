import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createAttendanceReport, fetchAttendanceReportsPage } from "@/features/college-admin/api/attendance-reports";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { AttendanceReportCreatePayload, AttendanceReportsQuery } from "@/features/college-admin/types/attendance-reports";

export function useAttendanceReportsPage(params?: AttendanceReportsQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.attendanceReports(params),
    queryFn: () => fetchAttendanceReportsPage(params),
  });
}

export function useCreateAttendanceReport(listParams?: AttendanceReportsQuery) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AttendanceReportCreatePayload) => createAttendanceReport(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.attendanceReports(listParams) });
    },
  });
}