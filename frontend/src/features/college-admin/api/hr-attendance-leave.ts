import { apiRequest } from "@/lib/api/client";

import type {
  HrAttendanceLeavePageQuery,
  HrEmployeeAttendancePage,
  HrLeaveApprovalPage,
  HrLeaveDecisionPayload,
  HrLeaveManagementPage,
} from "@/features/college-admin/types/hr-attendance-leave";

function buildQuery(params?: HrAttendanceLeavePageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchHrEmployeeAttendancePage(params?: HrAttendanceLeavePageQuery) {
  return apiRequest<HrEmployeeAttendancePage>(
    `/college-admin/hr-administration/attendance/page${buildQuery(params)}`,
  );
}

export function fetchHrLeaveManagementPage(params?: HrAttendanceLeavePageQuery) {
  return apiRequest<HrLeaveManagementPage>(
    `/college-admin/hr-administration/leave/management/page${buildQuery(params)}`,
  );
}

export function fetchHrLeaveApprovalPage(leaveRequestId?: string) {
  const q = leaveRequestId ? `?id=${encodeURIComponent(leaveRequestId)}` : "";
  return apiRequest<HrLeaveApprovalPage>(`/college-admin/hr-administration/leave/approval/page${q}`);
}

export function decideHrLeave(payload: HrLeaveDecisionPayload) {
  return apiRequest<{ leave_request_id: string; decision: string }>("/college-admin/hr-administration/leave/decide", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}