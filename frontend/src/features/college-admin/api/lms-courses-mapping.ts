import { apiRequest } from "@/lib/api/client";

import type {
  LmsCourseManagementPage,
  LmsCourseManagementPageQuery,
  LmsSubjectCourseMappingPage,
  LmsSubjectCourseMappingPageQuery,
} from "@/features/college-admin/types/lms-courses-mapping";

function buildQuery(params?: Record<string, string | number | undefined | null>) {
  const search = new URLSearchParams();
  if (!params) return "";
  for (const [key, value] of Object.entries(params)) {
    if (value != null && value !== "") search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchLmsCourseManagementPage(params?: LmsCourseManagementPageQuery) {
  return apiRequest<LmsCourseManagementPage>(
    `/college-admin/lms-administration/courses/management/page${buildQuery(params)}`,
  );
}

export function fetchLmsSubjectCourseMappingPage(params?: LmsSubjectCourseMappingPageQuery) {
  return apiRequest<LmsSubjectCourseMappingPage>(
    `/college-admin/lms-administration/subject-mapping/management/page${buildQuery(params)}`,
  );
}

export function postLmsSubjectAutoMap() {
  return apiRequest<{ created: number }>("/college-admin/lms-administration/subject-mapping/auto-map", {
    method: "POST",
  });
}

export function postLmsSubjectSaveMapping() {
  return apiRequest<{ created: number; updated: number }>(
    "/college-admin/lms-administration/subject-mapping/save",
    { method: "POST" },
  );
}