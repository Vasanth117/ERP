import { apiRequest } from "@/lib/api/client";

import type {
  LmsFacultyContentManagementPage,
  LmsProgressFacultyPageQuery,
  LmsStudentLearningProgressPage,
} from "@/features/college-admin/types/lms-progress-faculty";

function buildQuery(params?: Record<string, string | number | undefined | null>) {
  const search = new URLSearchParams();
  if (!params) return "";
  for (const [key, value] of Object.entries(params)) {
    if (value != null && value !== "") search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchLmsStudentLearningProgressPage(params?: LmsProgressFacultyPageQuery) {
  return apiRequest<LmsStudentLearningProgressPage>(
    `/college-admin/lms-administration/student-progress/management/page${buildQuery(params)}`,
  );
}

export function fetchLmsFacultyContentManagementPage(params?: LmsProgressFacultyPageQuery) {
  return apiRequest<LmsFacultyContentManagementPage>(
    `/college-admin/lms-administration/faculty-content/management/page${buildQuery(params)}`,
  );
}

export function postLmsFacultyContentApproveSelected() {
  return apiRequest<{ approved: number }>("/college-admin/lms-administration/faculty-content/approve-selected", {
    method: "POST",
  });
}