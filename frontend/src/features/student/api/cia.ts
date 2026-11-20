import { apiRequest } from "@/lib/api/client";

import { pageQuery } from "@/features/student/api/pagination";
import type { ApiPage } from "@/features/student/types/common";
import type {
  AssessmentComponent,
  CiaHistoryItem,
  CiaSchedule,
  CiaSummary,
  MarksCorrectionStatus,
  PublishedMark,
  SubjectInternalMarks,
} from "@/features/student/types/cia";

const BASE = "/students";

export function fetchCiaSummary() {
  return apiRequest<CiaSummary>(`${BASE}/me/cia/summary`);
}

export function fetchCiaSchedules() {
  return apiRequest<CiaSchedule[]>(`${BASE}/me/cia/schedules`);
}

export function fetchCiaMarks() {
  return apiRequest<PublishedMark[]>(`${BASE}/me/cia/marks`);
}

export function fetchCiaSubjectMarks() {
  return apiRequest<SubjectInternalMarks[]>(`${BASE}/me/cia/marks/subjects`);
}

export function fetchCiaCorrections(limit = 50, offset = 0) {
  return apiRequest<ApiPage<MarksCorrectionStatus>>(
    `${BASE}/me/cia/corrections?${pageQuery(limit, offset)}`,
  );
}

export function fetchCiaHistory(limit = 50, offset = 0) {
  return apiRequest<ApiPage<CiaHistoryItem>>(`${BASE}/me/cia/history?${pageQuery(limit, offset)}`);
}

export function fetchCiaComponents(assessmentId: string) {
  return apiRequest<AssessmentComponent[]>(
    `${BASE}/me/cia/assessments/${encodeURIComponent(assessmentId)}/components`,
  );
}

export function fetchCiaFeedback(assessmentId: string, componentId: string) {
  return apiRequest<Record<string, unknown>>(
    `${BASE}/me/cia/feedback/${encodeURIComponent(assessmentId)}/${encodeURIComponent(componentId)}`,
  );
}