import { apiRequest } from "@/lib/api/client";

import type {
  LmsLearningMaterialManagementPage,
  LmsLearningMaterialPageQuery,
  LmsVideoLectureManagementPage,
  LmsVideoLecturePageQuery,
} from "@/features/college-admin/types/lms-content";

function buildQuery(params?: Record<string, string | number | undefined | null>) {
  const search = new URLSearchParams();
  if (!params) return "";
  for (const [key, value] of Object.entries(params)) {
    if (value != null && value !== "") search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchLmsLearningMaterialManagementPage(params?: LmsLearningMaterialPageQuery) {
  return apiRequest<LmsLearningMaterialManagementPage>(
    `/college-admin/lms-administration/learning-materials/management/page${buildQuery(params)}`,
  );
}

export function fetchLmsVideoLectureManagementPage(params?: LmsVideoLecturePageQuery) {
  return apiRequest<LmsVideoLectureManagementPage>(
    `/college-admin/lms-administration/video-lectures/management/page${buildQuery(params)}`,
  );
}