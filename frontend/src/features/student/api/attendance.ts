import { apiRequest } from "@/lib/api/client";

import { pageQuery } from "@/features/student/api/pagination";
import type { ApiPage } from "@/features/student/types/common";
import type {
  AttendanceEligibility,
  AttendanceMark,
  AttendanceSemesterSummary,
  AttendanceShortage,
  AttendanceSummaryExport,
  DiscrepancyRequest,
  DiscrepancyRequestCreate,
  SubjectAttendanceDetail,
} from "@/features/student/types/attendance";

const BASE = "/students";

export function fetchAttendanceSummary() {
  return apiRequest<AttendanceSemesterSummary>(`${BASE}/me/attendance/summary`);
}

export function fetchSubjectAttendance() {
  return apiRequest<SubjectAttendanceDetail[]>(`${BASE}/me/attendance/subjects`);
}

export function fetchDailyAttendance(sessionDate: string) {
  return apiRequest<AttendanceMark[]>(`${BASE}/me/attendance/daily?session_date=${encodeURIComponent(sessionDate)}`);
}

export function fetchAttendanceHistory(limit = 50, offset = 0) {
  return apiRequest<ApiPage<AttendanceMark>>(
    `${BASE}/me/attendance/history?${pageQuery(limit, offset)}`,
  );
}

export function fetchAttendanceShortages() {
  return apiRequest<AttendanceShortage[]>(`${BASE}/me/attendance/shortages`);
}

export function fetchAttendanceEligibility() {
  return apiRequest<AttendanceEligibility>(`${BASE}/me/attendance/eligibility`);
}

export function fetchAttendanceExport() {
  return apiRequest<AttendanceSummaryExport>(`${BASE}/me/attendance/export`);
}

export function fetchDiscrepancyRequests(limit = 50, offset = 0) {
  return apiRequest<ApiPage<DiscrepancyRequest>>(
    `${BASE}/me/attendance/discrepancy-requests?${pageQuery(limit, offset)}`,
  );
}

export function submitDiscrepancyRequest(payload: DiscrepancyRequestCreate) {
  return apiRequest<DiscrepancyRequest>(`${BASE}/me/attendance/discrepancy-requests`, {
    method: "POST",
    body: payload,
  });
}