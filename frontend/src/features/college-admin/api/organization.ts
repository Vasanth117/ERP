import { apiRequest } from "@/lib/api/client";
import { itemsFromListResponse, totalFromListResponse } from "@/features/college-admin/api/normalize";
import type { AllDepartmentsListPage } from "@/features/college-admin/types/all-departments-list";
import type {
  CreateEditDepartmentFormValues,
  CreateEditDepartmentPage,
} from "@/features/college-admin/types/create-edit-department";
import type { DepartmentDetailsPage } from "@/features/college-admin/types/department-details";
import type {
  DepartmentHeadAssignmentPage,
  DepartmentHeadAssignmentSaveResult,
  DepartmentHeadAssignmentFormValues,
} from "@/features/college-admin/types/department-head-assignment";
import type { OrganizationalHierarchyPage } from "@/features/college-admin/types/organizational-hierarchy";
import type { ProgrammeCourseMappingPage } from "@/features/college-admin/types/programme-course-mapping";
import type {
  DepartmentFacultyAllocationPage,
  DepartmentFacultyAllocationSaveResult,
  DepartmentFacultyAllocationFormValues,
} from "@/features/college-admin/types/department-faculty-allocation";
import type { DepartmentStatusHistoryPage } from "@/features/college-admin/types/department-status-history";
import type { DepartmentResourceManagementPage } from "@/features/college-admin/types/department-resource-management";
import type { DepartmentManagementDashboardPage } from "@/features/college-admin/types/department-management-dashboard";
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

export async function fetchDepartmentDetailsPage(departmentId: string): Promise<DepartmentDetailsPage> {
  return apiRequest<DepartmentDetailsPage>(
    `/college-admin/departments/details/page?department_id=${encodeURIComponent(departmentId)}`,
  );
}

export async function fetchCreateEditDepartmentPage(
  departmentId: string | null,
): Promise<CreateEditDepartmentPage> {
  const qs = departmentId ? `?department_id=${encodeURIComponent(departmentId)}` : "";
  return apiRequest<CreateEditDepartmentPage>(`/college-admin/departments/create-edit/page${qs}`);
}

export async function saveCreateEditDepartment(payload: {
  department_id?: string | null;
  mode: "create" | "draft";
  form: CreateEditDepartmentFormValues;
}): Promise<CreateEditDepartmentPage> {
  return apiRequest<CreateEditDepartmentPage>("/college-admin/departments/create-edit/save", {
    method: "POST",
    body: payload,
  });
}

export async function fetchAllDepartmentsListPage(params?: {
  page?: number;
  search?: string;
  school_id?: string;
  type_filter?: string;
  status_filter?: string;
}): Promise<AllDepartmentsListPage> {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.search) qs.set("search", params.search);
  if (params?.school_id) qs.set("school_id", params.school_id);
  if (params?.type_filter) qs.set("type_filter", params.type_filter);
  if (params?.status_filter) qs.set("status_filter", params.status_filter);
  const suffix = qs.size ? `?${qs.toString()}` : "";
  return apiRequest<AllDepartmentsListPage>(`/college-admin/departments/all-departments/page${suffix}`);
}

export async function fetchDepartmentFacultyAllocationPage(params?: {
  page?: number;
  semester_label?: string;
  department_id?: string;
  designation_filter?: string;
}): Promise<DepartmentFacultyAllocationPage> {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.semester_label) qs.set("semester_label", params.semester_label);
  if (params?.department_id) qs.set("department_id", params.department_id);
  if (params?.designation_filter) qs.set("designation_filter", params.designation_filter);
  const suffix = qs.size ? `?${qs.toString()}` : "";
  return apiRequest<DepartmentFacultyAllocationPage>(
    `/college-admin/departments/faculty-allocation/page${suffix}`,
  );
}

export async function saveDepartmentFacultyAllocation(payload: {
  form: DepartmentFacultyAllocationFormValues;
  page?: number;
  semester_label?: string;
  department_id?: string;
  designation_filter?: string;
}): Promise<DepartmentFacultyAllocationSaveResult> {
  return apiRequest<DepartmentFacultyAllocationSaveResult>(
    "/college-admin/departments/faculty-allocation/save",
    { method: "POST", body: payload },
  );
}

export async function fetchDepartmentResourceManagementPage(
  departmentId?: string,
  view?: string,
): Promise<DepartmentResourceManagementPage> {
  const qs = new URLSearchParams();
  if (departmentId) qs.set("department_id", departmentId);
  if (view) qs.set("view", view);
  const suffix = qs.size ? `?${qs.toString()}` : "";
  return apiRequest<DepartmentResourceManagementPage>(
    `/college-admin/departments/resource-management/page${suffix}`,
  );
}

export async function fetchDepartmentStatusHistoryPage(params?: {
  page?: number;
  since_year?: string;
  department_id?: string;
  change_type_filter?: string;
  selected_department_id?: string;
}): Promise<DepartmentStatusHistoryPage> {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.since_year) qs.set("since_year", params.since_year);
  if (params?.department_id) qs.set("department_id", params.department_id);
  if (params?.change_type_filter) qs.set("change_type_filter", params.change_type_filter);
  if (params?.selected_department_id) qs.set("selected_department_id", params.selected_department_id);
  const suffix = qs.size ? `?${qs.toString()}` : "";
  return apiRequest<DepartmentStatusHistoryPage>(`/college-admin/departments/status-history/page${suffix}`);
}

export async function fetchProgrammeCourseMappingPage(
  departmentId?: string,
): Promise<ProgrammeCourseMappingPage> {
  const qs = departmentId ? `?department_id=${encodeURIComponent(departmentId)}` : "";
  return apiRequest<ProgrammeCourseMappingPage>(
    `/college-admin/departments/programme-course-mapping/page${qs}`,
  );
}

export async function fetchOrganizationalHierarchyPage(
  selectedNodeId?: string,
  editMode?: boolean,
): Promise<OrganizationalHierarchyPage> {
  const params = new URLSearchParams();
  if (selectedNodeId) params.set("selected_node_id", selectedNodeId);
  if (editMode) params.set("edit", "true");
  const qs = params.toString();
  return apiRequest<OrganizationalHierarchyPage>(
    `/college-admin/organization/hierarchy/page${qs ? `?${qs}` : ""}`,
  );
}

export async function fetchDepartmentHeadAssignmentPage(params?: {
  page?: number;
  selected_department_id?: string;
  faculty_user_id?: string;
}): Promise<DepartmentHeadAssignmentPage> {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.selected_department_id) qs.set("selected_department_id", params.selected_department_id);
  if (params?.faculty_user_id) qs.set("faculty_user_id", params.faculty_user_id);
  const suffix = qs.size ? `?${qs.toString()}` : "";
  return apiRequest<DepartmentHeadAssignmentPage>(
    `/college-admin/departments/head-assignment/page${suffix}`,
  );
}

export async function submitDepartmentHeadAssignment(payload: {
  department_id: string;
  form: DepartmentHeadAssignmentFormValues;
}): Promise<DepartmentHeadAssignmentSaveResult> {
  return apiRequest<DepartmentHeadAssignmentSaveResult>("/college-admin/departments/head-assignment/submit", {
    method: "POST",
    body: payload,
  });
}

export async function fetchDepartmentManagementDashboardPage(params?: {
  academic_year_label?: string;
  campus_id?: string;
  school_id?: string;
}): Promise<DepartmentManagementDashboardPage> {
  const qs = new URLSearchParams();
  if (params?.academic_year_label) qs.set("academic_year_label", params.academic_year_label);
  if (params?.campus_id) qs.set("campus_id", params.campus_id);
  if (params?.school_id) qs.set("school_id", params.school_id);
  const suffix = qs.size ? `?${qs.toString()}` : "";
  return apiRequest<DepartmentManagementDashboardPage>(
    `/college-admin/departments/management-dashboard/page${suffix}`,
  );
}