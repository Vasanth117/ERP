import { apiRequest } from "@/lib/api/client";

import type { ApiPage } from "@/features/college-admin/types/dashboard";

export type FacultyRecord = {
  record_id: string;
  user_id: string;
  employee_id?: string | null;
  faculty_code?: string | null;
  designation?: string | null;
  department_id?: string | null;
  employment_status: string;
  full_name: string;
  email: string;
  specialization?: string | null;
};

export function fetchFacultyList(limit = 50, offset = 0) {
  return apiRequest<ApiPage<FacultyRecord>>(
    `/college-admin/faculty-administration/faculty?limit=${limit}&offset=${offset}`,
  );
}

export function fetchFaculty(recordId: string) {
  return apiRequest<FacultyRecord>(
    `/college-admin/faculty-administration/faculty/${encodeURIComponent(recordId)}`,
  );
}

export function fetchFacultyHistory(recordId: string) {
  return apiRequest<unknown>(
    `/college-admin/faculty-administration/faculty/${encodeURIComponent(recordId)}/history`,
  );
}