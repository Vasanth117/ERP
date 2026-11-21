import { apiRequest } from "@/lib/api/client";

import type { ApiPage } from "@/features/college-admin/types/dashboard";
import type {
  FacultyEmployeeDashboardPage,
  FacultyEmployeeDashboardQuery,
} from "@/features/college-admin/types/faculty-employee-dashboard";
import type { EmployeeDirectoryPage, EmployeeDirectoryQuery } from "@/features/college-admin/types/employee-directory";
import type { FacultyDirectoryPage, FacultyDirectoryQuery } from "@/features/college-admin/types/faculty-directory";
import type { FacultyProfilePage } from "@/features/college-admin/types/faculty-profile";
import type {
  AddNewFacultyEmployeeCreateResult,
  AddNewFacultyEmployeeDraftPayload,
  AddNewFacultyEmployeePage,
} from "@/features/college-admin/types/add-new-faculty-employee";
import type { EmployeeProfileManagementPage } from "@/features/college-admin/types/employee-profile-management";
import type { DepartmentDesignationAssignmentPage } from "@/features/college-admin/types/department-designation-assignment";
import type {
  FacultySubjectAllocationPage,
  FacultySubjectAllocationQuery,
} from "@/features/college-admin/types/faculty-subject-allocation";
import type {
  FacultyWorkloadManagementPage,
  FacultyWorkloadManagementQuery,
} from "@/features/college-admin/types/faculty-workload-management";
import type { FacultyTimetablePage } from "@/features/college-admin/types/faculty-timetable";
import type { EmployeeDocumentVerificationPage } from "@/features/college-admin/types/employee-document-verification";
import type {
  EmployeeStatusManagementPage,
  EmployeeStatusManagementPageQuery,
} from "@/features/college-admin/types/employee-status-management";
import type {
  FacultyEmployeeHistoryPage,
  FacultyEmployeeHistoryPageQuery,
} from "@/features/college-admin/types/faculty-employee-history";

function buildEmployeeDirectoryQuery(params?: EmployeeDirectoryQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.search) search.set("search", params.search);
  if (params?.unit_id) search.set("unit_id", params.unit_id);
  if (params?.role) search.set("role", params.role);
  if (params?.type_filter) search.set("type_filter", params.type_filter);
  if (params?.status_filter) search.set("status_filter", params.status_filter);
  const q = search.toString();
  return q ? `?${q}` : "";
}

function buildFacultyDirectoryQuery(params?: FacultyDirectoryQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.search) search.set("search", params.search);
  if (params?.department_id) search.set("department_id", params.department_id);
  if (params?.designation) search.set("designation", params.designation);
  if (params?.status_filter) search.set("status_filter", params.status_filter);
  if (params?.academic_year_code) search.set("academic_year_code", params.academic_year_code);
  const q = search.toString();
  return q ? `?${q}` : "";
}

function buildFacultyDashboardQuery(params?: FacultyEmployeeDashboardQuery) {
  const search = new URLSearchParams();
  if (params?.academic_year_code) search.set("academic_year_code", params.academic_year_code);
  if (params?.department_id) search.set("department_id", params.department_id);
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const q = search.toString();
  return q ? `?${q}` : "";
}

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

export function fetchFacultyEmployeeDashboardPage(params?: FacultyEmployeeDashboardQuery) {
  return apiRequest<FacultyEmployeeDashboardPage>(
    `/college-admin/faculty-administration/dashboard/page${buildFacultyDashboardQuery(params)}`,
  );
}

export function fetchAddNewFacultyEmployeePage() {
  return apiRequest<AddNewFacultyEmployeePage>("/college-admin/faculty-administration/employees/new/page");
}

export function saveAddNewFacultyEmployeeDraft(payload: AddNewFacultyEmployeeDraftPayload) {
  return apiRequest<AddNewFacultyEmployeePage>("/college-admin/faculty-administration/employees/new/draft", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function createAddNewFacultyEmployee(payload: { draft_id: string; values?: Record<string, unknown> }) {
  return apiRequest<AddNewFacultyEmployeeCreateResult>(
    "/college-admin/faculty-administration/employees/new/create",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function fetchEmployeeProfileManagementPage(recordId?: string) {
  const suffix = recordId ? `?record_id=${encodeURIComponent(recordId)}` : "";
  return apiRequest<EmployeeProfileManagementPage>(
    `/college-admin/faculty-administration/employees/profile-management/page${suffix}`,
  );
}

function buildSubjectAllocationQuery(params?: FacultySubjectAllocationQuery) {
  const search = new URLSearchParams();
  if (params?.academic_year_label) search.set("academic_year_label", params.academic_year_label);
  if (params?.semester_label) search.set("semester_label", params.semester_label);
  if (params?.department_id) search.set("department_id", params.department_id);
  const q = search.toString();
  return q ? `?${q}` : "";
}

export function fetchDepartmentDesignationAssignmentPage(recordId?: string) {
  const suffix = recordId ? `?record_id=${encodeURIComponent(recordId)}` : "";
  return apiRequest<DepartmentDesignationAssignmentPage>(
    `/college-admin/faculty-administration/assignments/department-designation/page${suffix}`,
  );
}

export function saveDepartmentDesignationAssignment(payload: { record_id: string; values: Record<string, unknown> }) {
  return apiRequest<DepartmentDesignationAssignmentPage>(
    "/college-admin/faculty-administration/assignments/department-designation/save",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function fetchFacultySubjectAllocationPage(params?: FacultySubjectAllocationQuery) {
  return apiRequest<FacultySubjectAllocationPage>(
    `/college-admin/faculty-administration/assignments/subject-allocation/page${buildSubjectAllocationQuery(params)}`,
  );
}

export function autoSuggestFacultySubjectAllocation(payload: FacultySubjectAllocationQuery) {
  return apiRequest<FacultySubjectAllocationPage>(
    "/college-admin/faculty-administration/assignments/subject-allocation/auto-suggest",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

function buildWorkloadManagementQuery(params?: FacultyWorkloadManagementQuery) {
  const search = new URLSearchParams();
  if (params?.page != null && params.page > 1) search.set("page", String(params.page));
  if (params?.academic_year_label) search.set("academic_year_label", params.academic_year_label);
  if (params?.semester_label) search.set("semester_label", params.semester_label);
  const q = search.toString();
  return q ? `?${q}` : "";
}

export function fetchFacultyWorkloadManagementPage(params?: FacultyWorkloadManagementQuery) {
  return apiRequest<FacultyWorkloadManagementPage>(
    `/college-admin/faculty-administration/workload/management/page${buildWorkloadManagementQuery(params)}`,
  );
}

export function rebalanceFacultyWorkload(payload: {
  academic_year_label?: string;
  semester_label?: string;
}) {
  return apiRequest<FacultyWorkloadManagementPage>(
    "/college-admin/faculty-administration/workload/management/rebalance",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

function buildEmployeeStatusQuery(params?: EmployeeStatusManagementPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.selected_request_id) search.set("selected_request_id", params.selected_request_id);
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return suffix;
}

function buildFacultyEmployeeHistoryQuery(params?: FacultyEmployeeHistoryPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return suffix;
}

export function fetchEmployeeStatusManagementPage(params?: EmployeeStatusManagementPageQuery) {
  return apiRequest<EmployeeStatusManagementPage>(
    `/college-admin/faculty-administration/employees/status/page${buildEmployeeStatusQuery(params)}`,
  );
}

export function submitEmployeeStatusChange(payload: {
  record_id: string;
  new_status: string;
  reason: string;
  effective_date?: string;
  page?: number;
}) {
  return apiRequest<EmployeeStatusManagementPage>(
    "/college-admin/faculty-administration/employees/status/submit",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function approveEmployeeStatusChange(payload: { request_id: string; page?: number }) {
  return apiRequest<EmployeeStatusManagementPage>(
    "/college-admin/faculty-administration/employees/status/approve",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function fetchFacultyEmployeeHistoryPage(params?: FacultyEmployeeHistoryPageQuery) {
  return apiRequest<FacultyEmployeeHistoryPage>(
    `/college-admin/faculty-administration/employees/history/page${buildFacultyEmployeeHistoryQuery(params)}`,
  );
}

export function fetchEmployeeDocumentVerificationPage(documentId?: string) {
  const params = new URLSearchParams();
  if (documentId) params.set("document_id", documentId);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return apiRequest<EmployeeDocumentVerificationPage>(
    `/college-admin/faculty-administration/employees/documents/verification/page${suffix}`,
  );
}

export function saveEmployeeDocumentVerificationDecision(payload: {
  document_id: string;
  result: string;
  remarks?: string;
}) {
  return apiRequest<EmployeeDocumentVerificationPage>(
    "/college-admin/faculty-administration/employees/documents/verification/decide",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function verifyAllEmployeeDocuments() {
  return apiRequest<EmployeeDocumentVerificationPage>(
    "/college-admin/faculty-administration/employees/documents/verification/verify-all",
    { method: "POST", body: JSON.stringify({}) },
  );
}

export function fetchFacultyTimetablePage(recordId?: string, academicYear?: string, semester?: string) {
  const params = new URLSearchParams();
  if (recordId) params.set("record_id", recordId);
  if (academicYear) params.set("academic_year_label", academicYear);
  if (semester) params.set("semester_label", semester);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return apiRequest<FacultyTimetablePage>(`/college-admin/faculty-administration/timetable/page${suffix}`);
}

export function confirmFacultySubjectAllocation(payload: {
  academic_year_label: string;
  semester_label: string;
  department_id: string;
  allocations: { course_id: string; faculty_record_id: string }[];
}) {
  return apiRequest<FacultySubjectAllocationPage>(
    "/college-admin/faculty-administration/assignments/subject-allocation/confirm",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function saveEmployeeProfileManagement(payload: { record_id: string; values: Record<string, unknown> }) {
  return apiRequest<EmployeeProfileManagementPage>(
    "/college-admin/faculty-administration/employees/profile-management/save",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function fetchEmployeeDirectoryPage(params?: EmployeeDirectoryQuery) {
  return apiRequest<EmployeeDirectoryPage>(
    `/college-admin/faculty-administration/employees/directory/page${buildEmployeeDirectoryQuery(params)}`,
  );
}

export function fetchFacultyProfilePage(recordId: string) {
  return apiRequest<FacultyProfilePage>(
    `/college-admin/faculty-administration/faculty/profile/page?record_id=${encodeURIComponent(recordId)}`,
  );
}

export function fetchFacultyDirectoryPage(params?: FacultyDirectoryQuery) {
  return apiRequest<FacultyDirectoryPage>(
    `/college-admin/faculty-administration/faculty/directory/page${buildFacultyDirectoryQuery(params)}`,
  );
}

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