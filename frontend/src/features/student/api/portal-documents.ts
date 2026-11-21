import { apiRequest } from "@/lib/api/client";

import { pageQuery } from "@/features/student/api/pagination";
import type { ApiPage } from "@/features/student/types/common";

const BASE = "/students";

export type ProfileCorrectionRead = {
  request_id: string;
  field_name: string;
  proposed_value: string;
  reason: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ProfileCorrectionSubmit = {
  field_name: string;
  proposed_value: string;
  reason: string;
};

export type ProfileCorrectionSubmitResult = {
  request_id: string;
  status: string;
};

export type DocumentRequestItem = {
  id?: string;
  document_type?: string;
  status?: string;
  requested_at?: string;
  [key: string]: unknown;
};

export function fetchProfileCorrections() {
  return apiRequest<ProfileCorrectionRead[]>(`${BASE}/me/profile-corrections`);
}

export function submitProfileCorrection(payload: ProfileCorrectionSubmit) {
  return apiRequest<ProfileCorrectionSubmitResult>(`${BASE}/me/profile-corrections`, {
    method: "POST",
    body: payload,
  });
}

export function fetchDocumentRequests(limit = 20, offset = 0) {
  return apiRequest<ApiPage<DocumentRequestItem>>(
    `${BASE}/me/documents/requests?${pageQuery(limit, offset)}`,
  );
}

export function fetchAuthorizedDocuments() {
  return apiRequest<unknown[]>(`${BASE}/me/documents/authorized`);
}