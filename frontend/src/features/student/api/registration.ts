import { apiRequest } from "@/lib/api/client";

import { pageQuery } from "@/features/student/api/pagination";
import type { ApiPage } from "@/features/student/types/common";
import type {
  AvailableCourse,
  CourseRegistration,
  ElectiveGroup,
  ElectiveOption,
  RegistrationEligibility,
  RegistrationHistory,
  RegistrationSelectionInput,
  RegistrationSubmit,
  RegistrationValidation,
} from "@/features/student/types/registration";

const BASE = "/students";

export async function fetchRegistrationEligibility(): Promise<RegistrationEligibility> {
  return apiRequest<RegistrationEligibility>(`${BASE}/me/registration/eligibility`);
}

export async function fetchAvailableCourses(): Promise<AvailableCourse[]> {
  return apiRequest<AvailableCourse[]>(`${BASE}/me/registration/available-courses`);
}

export async function fetchElectiveGroups(): Promise<ElectiveGroup[]> {
  return apiRequest<ElectiveGroup[]>(`${BASE}/me/registration/elective-groups`);
}

export async function fetchElectiveOptions(groupId: string): Promise<ElectiveOption[]> {
  return apiRequest<ElectiveOption[]>(
    `${BASE}/me/registration/elective-groups/${encodeURIComponent(groupId)}/options`,
  );
}

export async function validateRegistration(
  selections: RegistrationSelectionInput[],
): Promise<RegistrationValidation> {
  return apiRequest<RegistrationValidation>(`${BASE}/me/registration/validate`, {
    method: "POST",
    body: selections,
  });
}

export async function submitRegistration(
  selections: RegistrationSelectionInput[],
): Promise<RegistrationSubmit> {
  return apiRequest<RegistrationSubmit>(`${BASE}/me/registration/submit`, {
    method: "POST",
    body: selections,
  });
}

export async function cancelCourseRegistration(courseId: string): Promise<CourseRegistration> {
  return apiRequest<CourseRegistration>(
    `${BASE}/me/registration/courses/${encodeURIComponent(courseId)}/cancel`,
    { method: "POST" },
  );
}

export async function fetchConfirmedRegistrations(): Promise<CourseRegistration[]> {
  return apiRequest<CourseRegistration[]>(`${BASE}/me/registration/courses`);
}

export async function fetchRegistrationHistory(
  limit = 50,
  offset = 0,
): Promise<ApiPage<RegistrationHistory>> {
  return apiRequest<ApiPage<RegistrationHistory>>(
    `${BASE}/me/registration/history?${pageQuery(limit, offset)}`,
  );
}