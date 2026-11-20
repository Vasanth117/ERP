import { apiRequest } from "@/lib/api/client";

import { pageQuery } from "@/features/student/api/pagination";
import type {
  AcademicDetails,
  AcademicEligibility,
  EnrollmentHistory,
  EnrollmentRequest,
  EnrollmentRequestCreate,
  EnrollmentStatus,
} from "@/features/student/types/academics";
import type { ApiPage } from "@/features/student/types/common";

const BASE = "/students";

export async function fetchAcademicDetails(): Promise<AcademicDetails> {
  return apiRequest<AcademicDetails>(`${BASE}/me/academics`);
}

export async function fetchEnrollmentStatus(): Promise<EnrollmentStatus> {
  return apiRequest<EnrollmentStatus>(`${BASE}/me/academics/status`);
}

export async function fetchEnrollmentHistory(
  limit = 50,
  offset = 0,
): Promise<ApiPage<EnrollmentHistory>> {
  return apiRequest<ApiPage<EnrollmentHistory>>(
    `${BASE}/me/academics/enrollment-history?${pageQuery(limit, offset)}`,
  );
}

export async function fetchAcademicEligibility(): Promise<AcademicEligibility> {
  return apiRequest<AcademicEligibility>(`${BASE}/me/academics/eligibility`);
}

export async function fetchEnrollmentRequests(
  limit = 50,
  offset = 0,
): Promise<ApiPage<EnrollmentRequest>> {
  return apiRequest<ApiPage<EnrollmentRequest>>(
    `${BASE}/me/academics/enrollment-requests?${pageQuery(limit, offset)}`,
  );
}

export async function submitEnrollmentRequest(
  payload: EnrollmentRequestCreate,
): Promise<EnrollmentRequest> {
  return apiRequest<EnrollmentRequest>(`${BASE}/me/academics/enrollment-requests`, {
    method: "POST",
    body: payload,
  });
}

export async function fetchEnrollmentRequest(requestId: string): Promise<EnrollmentRequest> {
  return apiRequest<EnrollmentRequest>(`${BASE}/me/academics/enrollment-requests/${requestId}`);
}