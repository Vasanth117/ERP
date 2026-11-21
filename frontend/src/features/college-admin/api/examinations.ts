import { apiRequest } from "@/lib/api/client";

import type {
  ExamRegistrationManagementPage,
  ExamRegistrationManagementPageQuery,
} from "@/features/college-admin/types/exam-registration-management";

function buildQuery(params?: ExamRegistrationManagementPageQuery): string {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.session_id) search.set("session_id", params.session_id);
  if (params?.status) search.set("status", params.status);
  if (params?.programme_code) search.set("programme_code", params.programme_code);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchExamRegistrationManagementPage(params?: ExamRegistrationManagementPageQuery) {
  return apiRequest<ExamRegistrationManagementPage>(
    `/college-admin/examination-administration/registrations/page${buildQuery(params)}`,
  );
}

export function confirmSelectedExamRegistrations(payload: {
  registration_ids: string[];
  session_id: string;
  status?: string;
  programme_code?: string;
  page?: number;
}) {
  return apiRequest<ExamRegistrationManagementPage>(
    "/college-admin/examination-administration/registrations/confirm-selected",
    { method: "POST", body: JSON.stringify(payload) },
  );
}