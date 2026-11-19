import { apiRequest } from "@/lib/api/client";

import type { ApiPage } from "@/features/college-admin/types/dashboard";

export type StudentRecord = {
  record_id: string;
  student_id?: string;
  full_name?: string;
  email?: string;
  status?: string;
  programme_id?: string;
};

export type AdmissionRecord = {
  admission_id: string;
  applicant_name?: string;
  status?: string;
  programme_id?: string;
};

export function fetchStudents(limit = 50, offset = 0) {
  return apiRequest<ApiPage<StudentRecord>>(
    `/college-admin/student-administration/students?limit=${limit}&offset=${offset}`,
  );
}

export function fetchStudent(recordId: string) {
  return apiRequest<StudentRecord>(
    `/college-admin/student-administration/students/${encodeURIComponent(recordId)}`,
  );
}

export function fetchAdmissions(limit = 50, offset = 0) {
  return apiRequest<ApiPage<AdmissionRecord>>(
    `/college-admin/student-administration/admissions?limit=${limit}&offset=${offset}`,
  );
}