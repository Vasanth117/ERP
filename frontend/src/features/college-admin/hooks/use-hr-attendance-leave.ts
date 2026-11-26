import { useCollegeAdminMutation as useMutation } from "@/features/college-admin/hooks/use-college-admin-mutation";
import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useQueryClient } from "@tanstack/react-query";

import {
  decideHrLeave,
  fetchHrEmployeeAttendancePage,
  fetchHrLeaveApprovalPage,
  fetchHrLeaveManagementPage,
} from "@/features/college-admin/api/hr-attendance-leave";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  HrAttendanceLeavePageQuery,
  HrLeaveDecisionPayload,
} from "@/features/college-admin/types/hr-attendance-leave";

export function useHrEmployeeAttendancePage(params?: HrAttendanceLeavePageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hrEmployeeAttendancePage(params),
    queryFn: () => fetchHrEmployeeAttendancePage(params),
  });
}

export function useHrLeaveManagementPage(params?: HrAttendanceLeavePageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hrLeaveManagementPage(params),
    queryFn: () => fetchHrLeaveManagementPage(params),
  });
}

export function useHrLeaveApprovalPage(leaveRequestId?: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hrLeaveApprovalPage(leaveRequestId),
    queryFn: () => fetchHrLeaveApprovalPage(leaveRequestId),
  });
}

export function useDecideHrLeave(leaveRequestId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: HrLeaveDecisionPayload) => decideHrLeave(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.hrLeaveApprovalPage(leaveRequestId) });
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.hrLeaveManagementPage() });
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.hrDashboardPage() });
    },
  });
}