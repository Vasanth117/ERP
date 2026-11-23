import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  decideAttendanceCorrection,
  fetchAttendanceApprovalPage,
  fetchAttendanceCorrectionRequestsPage,
} from "@/features/college-admin/api/attendance-corrections";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  AttendanceCorrectionDecidePayload,
  AttendanceCorrectionsListQuery,
} from "@/features/college-admin/types/attendance-corrections";

export function useAttendanceCorrectionRequestsPage(params?: AttendanceCorrectionsListQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.attendanceCorrectionRequests(params),
    queryFn: () => fetchAttendanceCorrectionRequestsPage(params),
  });
}

export function useAttendanceApprovalPage(requestId?: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.attendanceApproval(requestId),
    queryFn: () => fetchAttendanceApprovalPage(requestId),
  });
}

export function useDecideAttendanceCorrection(requestId?: string, listParams?: AttendanceCorrectionsListQuery) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AttendanceCorrectionDecidePayload) => decideAttendanceCorrection(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.attendanceApproval(requestId) });
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.attendanceCorrectionRequests(listParams) });
    },
  });
}