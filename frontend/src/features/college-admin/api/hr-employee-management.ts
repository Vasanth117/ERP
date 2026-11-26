import { apiRequest } from "@/lib/api/client";

import type { EmployeeDirectoryPage } from "@/features/college-admin/types/employee-directory";
import type { HrEmployeeManagementQuery } from "@/features/college-admin/types/hr-employee-management";

function buildQuery(params?: HrEmployeeManagementQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.search) search.set("search", params.search);
  if (params?.department_id) search.set("department_id", params.department_id);
  if (params?.type_filter) search.set("type_filter", params.type_filter);
  if (params?.status_filter) search.set("status_filter", params.status_filter);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchHrEmployeeManagementPage(params?: HrEmployeeManagementQuery) {
  return apiRequest<EmployeeDirectoryPage>(
    `/college-admin/hr-administration/employees/management/page${buildQuery(params)}`,
  );
}