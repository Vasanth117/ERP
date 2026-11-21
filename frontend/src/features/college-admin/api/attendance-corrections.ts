import { apiRequest } from "@/lib/api/client";

import type {
  AttendanceApprovalPage,
  AttendanceCorrectionDecidePayload,
  AttendanceCorrectionRequestsPage,
  AttendanceCorrectionsListQuery,
} from "@/features/college-admin/types/attendance-corrections";

function buildListQuery(params?: AttendanceCorrectionsListQuery): string {
  if (!params) return "";
  const q = new URLSearchParams();
  if (params.page != null) q.set("page", String(params.page));
  if (params.page_size != null) q.set("page_size", String(params.page_size));
  const s = q.toString();
  return s ? `?${s}` : "";
}

export function fetchAttendanceCorrectionRequestsPage(params?: AttendanceCorrectionsListQuery) {
  return apiRequest<AttendanceCorrectionRequestsPage>(
    `/college-admin/attendance-administration/corrections/requests/page${buildListQuery(params)}`,
  );
}

export function fetchAttendanceApprovalPage(requestId?: string) {
  const q = requestId ? `?request_id=${encodeURIComponent(requestId)}` : "";
  return apiRequest<AttendanceApprovalPage>(`/college-admin/attendance-administration/corrections/approval/page${q}`);
}

export function decideAttendanceCorrection(payload: AttendanceCorrectionDecidePayload) {
  return apiRequest<{ request_id: string; decision: string }>(
    "/college-admin/attendance-administration/corrections/decide",
    {
      method: "POST",
      body: JSON.stringify({
        request_id: payload.request_id,
        decision: payload.decision,
        reviewer_note: payload.reviewer_note ?? null,
      }),
    },
  );
}