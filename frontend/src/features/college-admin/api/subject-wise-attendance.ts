import { apiRequest } from "@/lib/api/client";

import type {
  SubjectWiseAttendancePage,
  SubjectWiseAttendanceQuery,
} from "@/features/college-admin/types/subject-wise-attendance";

function buildQuery(params?: SubjectWiseAttendanceQuery): string {
  if (!params) return "";
  const q = new URLSearchParams();
  if (params.term_key) q.set("term_key", params.term_key);
  if (params.scope_key) q.set("scope_key", params.scope_key);
  const s = q.toString();
  return s ? `?${s}` : "";
}

export function fetchSubjectWiseAttendancePage(params?: SubjectWiseAttendanceQuery) {
  return apiRequest<SubjectWiseAttendancePage>(
    `/college-admin/attendance-administration/subject-wise/page${buildQuery(params)}`,
  );
}