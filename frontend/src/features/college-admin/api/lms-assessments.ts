import { apiRequest } from "@/lib/api/client";

import type {
  LmsAssessmentManagementPage,
  LmsAssignmentManagementPage,
  LmsAssessmentsPageQuery,
  LmsQuizManagementPage,
} from "@/features/college-admin/types/lms-assessments";

function buildQuery(params?: Record<string, string | number | undefined | null>) {
  const search = new URLSearchParams();
  if (!params) return "";
  for (const [key, value] of Object.entries(params)) {
    if (value != null && value !== "") search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchLmsAssignmentManagementPage(params?: LmsAssessmentsPageQuery) {
  return apiRequest<LmsAssignmentManagementPage>(
    `/college-admin/lms-administration/assignments/management/page${buildQuery(params)}`,
  );
}

export function fetchLmsQuizManagementPage(params?: LmsAssessmentsPageQuery) {
  return apiRequest<LmsQuizManagementPage>(
    `/college-admin/lms-administration/quizzes/management/page${buildQuery(params)}`,
  );
}

export function fetchLmsAssessmentManagementPage(params?: LmsAssessmentsPageQuery) {
  return apiRequest<LmsAssessmentManagementPage>(
    `/college-admin/lms-administration/assessments/management/page${buildQuery(params)}`,
  );
}