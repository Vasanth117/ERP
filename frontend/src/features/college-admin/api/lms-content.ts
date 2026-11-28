import { apiRequest } from "@/lib/api/client";
import { apiBaseUrl } from "@/lib/env";
import { applyAuthHeaders } from "@/lib/api/auth-headers";

import type {
  LmsLearningMaterialManagementPage,
  LmsLearningMaterialPageQuery,
  LmsUnitChapterManagementPage,
  LmsUnitChapterPageQuery,
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

export function fetchLmsUnitChapterManagementPage(params?: LmsUnitChapterPageQuery) {
  return apiRequest<LmsUnitChapterManagementPage>(
    `/college-admin/lms-administration/units-chapters/management/page${buildQuery(params)}`,
  );
}

async function downloadCsv(path: string, filename: string) {
  const headers = new Headers();
  applyAuthHeaders(headers);
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    method: "GET",
    headers,
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Export failed (${response.status})`);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function downloadLmsLearningMaterialsExport() {
  return downloadCsv("/college-admin/lms-administration/learning-materials/management/export", "lms-learning-materials.csv");
}

export function downloadLmsVideoLecturesExport() {
  return downloadCsv("/college-admin/lms-administration/video-lectures/management/export", "lms-video-lectures.csv");
}

export function downloadLmsUnitsChaptersExport(params?: LmsUnitChapterPageQuery) {
  const suffix = params?.course_code ? `-${params.course_code}` : "";
  return downloadCsv(
    `/college-admin/lms-administration/units-chapters/management/export${buildQuery(params)}`,
    `lms-units-chapters${suffix}.csv`,
  );
}

export type LmsContentUploadPayload = {
  course_code: string;
  title: string;
  unit_no?: number;
  material_kind: "document" | "video";
  file: File;
};

export function uploadLmsLearningMaterial(payload: LmsContentUploadPayload) {
  const formData = new FormData();
  formData.append("course_code", payload.course_code);
  formData.append("title", payload.title);
  formData.append("material_kind", payload.material_kind);
  if (payload.unit_no != null) {
    formData.append("unit_no", String(payload.unit_no));
  }
  formData.append("file", payload.file);
  return apiRequest<{ material_id: string }>("/college-admin/lms-administration/learning-materials/management/upload", {
    method: "POST",
    rawBody: formData,
  });
}

export function fetchLmsVideoLectureManagementPage(params?: LmsVideoLecturePageQuery) {
  return apiRequest<LmsVideoLectureManagementPage>(
    `/college-admin/lms-administration/video-lectures/management/page${buildQuery(params)}`,
  );
}