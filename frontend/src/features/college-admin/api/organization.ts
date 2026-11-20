import { apiRequest } from "@/lib/api/client";
import { itemsFromListResponse, totalFromListResponse } from "@/features/college-admin/api/normalize";
import type { ApiPage } from "@/features/college-admin/types/dashboard";

export type Department = {
  department_id: string;
  department_code: string;
  name: string;
  status: string;
  parent_department_id: string | null;
  organization_unit_id: string | null;
  head_user_id: string | null;
  campus_ids: string[];
  programme_codes: string[];
  updated_at: string;
};

export type OrganizationUnit = {
  unit_id: string;
  unit_code: string;
  name: string;
  unit_type: string;
  parent_unit_id: string | null;
};

export async function fetchDepartmentsPage(
  limit = 200,
  offset = 0,
): Promise<ApiPage<Department>> {
  return apiRequest(
    `/college-admin/departments?limit=${limit}&offset=${offset}`,
  );
}

export async function fetchDepartments(): Promise<Department[]> {
  const page = await fetchDepartmentsPage();
  return itemsFromListResponse<Department>(page);
}

export async function fetchDepartmentsTotal(): Promise<number> {
  const page = await fetchDepartmentsPage(1, 0);
  return totalFromListResponse(page);
}

export async function fetchDepartment(id: string): Promise<Department> {
  return apiRequest(`/college-admin/departments/${encodeURIComponent(id)}`);
}

export async function createDepartment(payload: {
  department_code: string;
  name: string;
  parent_department_id?: string;
  organization_unit_id?: string;
}): Promise<Department> {
  return apiRequest("/college-admin/departments", {
    method: "POST",
    body: payload,
  });
}

export async function updateDepartment(
  id: string,
  payload: Partial<{
    name: string;
    status: string;
    parent_department_id: string | null;
  }>,
): Promise<Department> {
  return apiRequest(`/college-admin/departments/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: payload,
  });
}

export async function fetchOrganizationUnits(): Promise<OrganizationUnit[]> {
  return apiRequest("/college-admin/organization/units");
}

export async function createOrganizationUnit(payload: {
  unit_code: string;
  name: string;
  unit_type: string;
  parent_unit_id?: string;
}): Promise<OrganizationUnit> {
  return apiRequest("/college-admin/organization/units", {
    method: "POST",
    body: payload,
  });
}

export async function fetchDepartmentHistory(id: string) {
  return apiRequest(`/college-admin/departments/${encodeURIComponent(id)}/history`);
}