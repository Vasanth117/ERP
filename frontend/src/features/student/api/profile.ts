import { apiRequest } from "@/lib/api/client";

import { pageQuery } from "@/features/student/api/pagination";
import type { ApiPage } from "@/features/student/types/common";
import type { StudentActivity } from "@/features/student/types/dashboard";
import type { StudentProfile, StudentProfileUpdate } from "@/features/student/types/profile";

const BASE = "/students";

export async function fetchStudentProfile(): Promise<StudentProfile> {
  return apiRequest<StudentProfile>(`${BASE}/me/profile`);
}

export async function updateStudentProfile(
  payload: StudentProfileUpdate,
): Promise<StudentProfile> {
  return apiRequest<StudentProfile>(`${BASE}/me/profile`, {
    method: "PATCH",
    body: payload,
  });
}

export async function fetchProfileActivities(
  limit = 50,
  offset = 0,
): Promise<ApiPage<StudentActivity>> {
  return apiRequest<ApiPage<StudentActivity>>(
    `${BASE}/me/profile/activities?${pageQuery(limit, offset)}`,
  );
}