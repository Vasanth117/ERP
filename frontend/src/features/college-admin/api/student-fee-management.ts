import { apiRequest } from "@/lib/api/client";

import type {
  StudentFeeManagementPage,
  StudentFeeManagementPageQuery,
} from "@/features/college-admin/types/student-fee-management";

export function fetchStudentFeeManagementPage(params?: StudentFeeManagementPageQuery) {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  const qs = search.toString();
  return apiRequest<StudentFeeManagementPage>(
    `/college-admin/finance-administration/assessments/page${qs ? `?${qs}` : ""}`,
  );
}