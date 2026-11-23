import { apiRequest } from "@/lib/api/client";

import type { ApiPage } from "@/features/college-admin/types/dashboard";
import type { AllStudentsListPage } from "@/features/college-admin/types/all-students-list";
import type {
  NewStudentRegistrationDraftPayload,
  NewStudentRegistrationPage,
} from "@/features/college-admin/types/new-student-registration";
import type { StudentDocumentVerificationPage } from "@/features/college-admin/types/student-document-verification";
import type { StudentProfileManagementPage } from "@/features/college-admin/types/student-profile-management";
import type { StudentAdmissionPage, StudentAdmissionPageQuery } from "@/features/college-admin/types/student-admission";
import type {
  BatchSectionAllocationPage,
  BatchSectionAllocationPageQuery,
  BatchSectionAllocationRulesPayload,
} from "@/features/college-admin/types/batch-section-allocation";
import type {
  StudentEnrollmentManagementPage,
  StudentEnrollmentManagementPageQuery,
} from "@/features/college-admin/types/student-enrollment-management";
import type {
  StudentPromotionManagementPage,
  StudentPromotionManagementPageQuery,
  StudentPromotionPromotePayload,
} from "@/features/college-admin/types/student-promotion-management";
import type {
  StudentStatusApprovePayload,
  StudentStatusChangeSubmitPayload,
  StudentStatusManagementPage,
  StudentStatusManagementPageQuery,
} from "@/features/college-admin/types/student-status-management";
import type {
  StudentWithdrawalDiscontinuationPage,
  StudentWithdrawalPageQuery,
  StudentWithdrawalSavePayload,
  StudentWithdrawalSubmitPayload,
} from "@/features/college-admin/types/student-withdrawal-discontinuation";
import type {
  StudentIdCardBulkPrintPayload,
  StudentIdCardIssuePayload,
  StudentIdCardManagementPage,
  StudentIdCardManagementPageQuery,
} from "@/features/college-admin/types/student-id-card-management";
import type { StudentAcademicHistoryPage } from "@/features/college-admin/types/student-academic-history";
import type {
  StudentTransferManagementPage,
  StudentTransferManagementPageQuery,
  StudentTransferReviewPayload,
} from "@/features/college-admin/types/student-transfer-management";
import type { StudentDetailsPage } from "@/features/college-admin/types/student-details";
import type {
  StudentAdministrationDashboardPage,
  StudentAdministrationDashboardQuery,
} from "@/features/college-admin/types/student-administration-dashboard";

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

function buildStudentDashboardQuery(params?: StudentAdministrationDashboardQuery) {
  const search = new URLSearchParams();
  if (params?.academic_year_code) search.set("academic_year_code", params.academic_year_code);
  if (params?.programme_code) search.set("programme_code", params.programme_code);
  if (params?.study_year) search.set("study_year", params.study_year);
  const q = search.toString();
  return q ? `?${q}` : "";
}

export function fetchStudentAdministrationDashboardPage(params?: StudentAdministrationDashboardQuery) {
  return apiRequest<StudentAdministrationDashboardPage>(
    `/college-admin/student-administration/dashboard/page${buildStudentDashboardQuery(params)}`,
  );
}

export function fetchStudentProfileManagementPage(recordId?: string) {
  const suffix = recordId ? `?record_id=${encodeURIComponent(recordId)}` : "";
  return apiRequest<StudentProfileManagementPage>(
    `/college-admin/student-administration/students/profile-management/page${suffix}`,
  );
}

export function fetchStudentDocumentVerificationPage(recordId?: string, documentKey?: string) {
  const params = new URLSearchParams();
  if (recordId) params.set("record_id", recordId);
  if (documentKey) params.set("document_key", documentKey);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return apiRequest<StudentDocumentVerificationPage>(
    `/college-admin/student-administration/students/documents/verification/page${suffix}`,
  );
}

export function saveStudentDocumentVerificationDecision(payload: {
  record_id: string;
  document_key: string;
  result: string;
  remarks?: string;
}) {
  return apiRequest<StudentDocumentVerificationPage>(
    "/college-admin/student-administration/students/documents/verification/decide",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function verifyAllStudentDocuments(recordId: string) {
  return apiRequest<StudentDocumentVerificationPage>(
    "/college-admin/student-administration/students/documents/verification/verify-all",
    { method: "POST", body: JSON.stringify({ record_id: recordId }) },
  );
}

export function saveStudentProfileManagement(payload: {
  record_id: string;
  values: Record<string, unknown>;
}) {
  return apiRequest<StudentProfileManagementPage>(
    "/college-admin/student-administration/students/profile-management/save",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function fetchStudentDetailsPage(recordId: string) {
  return apiRequest<StudentDetailsPage>(
    `/college-admin/student-administration/students/details/page?record_id=${encodeURIComponent(recordId)}`,
  );
}

export function fetchStudentAcademicHistoryPage(recordId: string) {
  return apiRequest<StudentAcademicHistoryPage>(
    `/college-admin/student-administration/students/academic-history/page?record_id=${encodeURIComponent(recordId)}`,
  );
}

function buildStudentAdmissionQuery(params?: StudentAdmissionPageQuery) {
  const searchParams = new URLSearchParams();
  if (params?.page && params.page > 1) searchParams.set("page", String(params.page));
  if (params?.academic_year_code) searchParams.set("academic_year_code", params.academic_year_code);
  if (params?.programme_code) searchParams.set("programme_code", params.programme_code);
  if (params?.quota_filter) searchParams.set("quota_filter", params.quota_filter);
  if (params?.status_filter) searchParams.set("status_filter", params.status_filter);
  if (params?.search) searchParams.set("search", params.search);
  const suffix = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return suffix;
}

export function fetchNewStudentRegistrationPage(admissionId?: string) {
  const suffix = admissionId ? `?admission_id=${encodeURIComponent(admissionId)}` : "";
  return apiRequest<NewStudentRegistrationPage>(
    `/college-admin/student-administration/registrations/new/page${suffix}`,
  );
}

export function saveNewStudentRegistrationDraft(payload: NewStudentRegistrationDraftPayload) {
  return apiRequest<NewStudentRegistrationPage>("/college-admin/student-administration/registrations/new/draft", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function fetchStudentAdmissionPage(params?: StudentAdmissionPageQuery) {
  return apiRequest<StudentAdmissionPage>(
    `/college-admin/student-administration/admissions/page${buildStudentAdmissionQuery(params)}`,
  );
}

function buildStudentEnrollmentQuery(params?: StudentEnrollmentManagementPageQuery) {
  const searchParams = new URLSearchParams();
  if (params?.page && params.page > 1) searchParams.set("page", String(params.page));
  if (params?.term_key) searchParams.set("term_key", params.term_key);
  if (params?.programme_code) searchParams.set("programme_code", params.programme_code);
  const suffix = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return suffix;
}

export function fetchStudentEnrollmentManagementPage(params?: StudentEnrollmentManagementPageQuery) {
  return apiRequest<StudentEnrollmentManagementPage>(
    `/college-admin/student-administration/students/enrollment/page${buildStudentEnrollmentQuery(params)}`,
  );
}

export function bulkEnrollStudents(payload: {
  record_ids: string[];
  term_key: string;
  programme_code?: string;
  page?: number;
}) {
  return apiRequest<StudentEnrollmentManagementPage>(
    "/college-admin/student-administration/students/enrollment/enroll-selected",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

function buildBatchSectionAllocationQuery(params?: BatchSectionAllocationPageQuery) {
  const searchParams = new URLSearchParams();
  if (params?.section_page && params.section_page > 1) {
    searchParams.set("section_page", String(params.section_page));
  }
  if (params?.unallocated_page && params.unallocated_page > 1) {
    searchParams.set("unallocated_page", String(params.unallocated_page));
  }
  const suffix = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return suffix;
}

export function fetchBatchSectionAllocationPage(params?: BatchSectionAllocationPageQuery) {
  return apiRequest<BatchSectionAllocationPage>(
    `/college-admin/student-administration/students/batch-section-allocation/page${buildBatchSectionAllocationQuery(params)}`,
  );
}

export function autoAllocateBatchSections(sectionPage?: number, unallocatedPage?: number) {
  const searchParams = new URLSearchParams();
  if (sectionPage && sectionPage > 1) searchParams.set("section_page", String(sectionPage));
  if (unallocatedPage && unallocatedPage > 1) searchParams.set("unallocated_page", String(unallocatedPage));
  const suffix = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return apiRequest<BatchSectionAllocationPage>(
    `/college-admin/student-administration/students/batch-section-allocation/auto-allocate${suffix}`,
    { method: "POST" },
  );
}

export function confirmBatchSectionAllocation(payload: BatchSectionAllocationRulesPayload) {
  return apiRequest<BatchSectionAllocationPage>(
    "/college-admin/student-administration/students/batch-section-allocation/confirm",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

function buildStudentTransferQuery(params?: StudentTransferManagementPageQuery) {
  const searchParams = new URLSearchParams();
  if (params?.page && params.page > 1) searchParams.set("page", String(params.page));
  if (params?.selected_request_key) searchParams.set("selected_request_key", params.selected_request_key);
  const suffix = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return suffix;
}

export function fetchStudentTransferManagementPage(params?: StudentTransferManagementPageQuery) {
  return apiRequest<StudentTransferManagementPage>(
    `/college-admin/student-administration/students/transfers/page${buildStudentTransferQuery(params)}`,
  );
}

export function saveStudentTransferReview(payload: StudentTransferReviewPayload) {
  return apiRequest<StudentTransferManagementPage>(
    "/college-admin/student-administration/students/transfers/review",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function fetchStudentTransferCreatePage() {
  return apiRequest<import("@/features/college-admin/types/student-transfer-create").StudentTransferCreatePage>(
    "/college-admin/student-administration/students/transfers/create/page",
  );
}

export function createStudentTransferRequest(
  payload: import("@/features/college-admin/types/student-transfer-create").StudentTransferCreatePayload,
) {
  return apiRequest<import("@/features/college-admin/types/student-transfer-create").StudentTransferCreateResult>(
    "/college-admin/student-administration/students/transfers",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

function buildStudentPromotionQuery(params?: StudentPromotionManagementPageQuery) {
  const searchParams = new URLSearchParams();
  if (params?.transition_key) searchParams.set("transition_key", params.transition_key);
  if (params?.programme_code) searchParams.set("programme_code", params.programme_code);
  const suffix = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return suffix;
}

export function fetchStudentPromotionManagementPage(params?: StudentPromotionManagementPageQuery) {
  return apiRequest<StudentPromotionManagementPage>(
    `/college-admin/student-administration/students/promotion/page${buildStudentPromotionQuery(params)}`,
  );
}

export function previewStudentPromotion(params?: StudentPromotionManagementPageQuery) {
  const searchParams = new URLSearchParams();
  if (params?.transition_key) searchParams.set("transition_key", params.transition_key);
  if (params?.programme_code) searchParams.set("programme_code", params.programme_code);
  const suffix = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return apiRequest<StudentPromotionManagementPage>(
    `/college-admin/student-administration/students/promotion/preview${suffix}`,
    { method: "POST" },
  );
}

export function promoteEligibleStudents(payload: StudentPromotionPromotePayload) {
  return apiRequest<StudentPromotionManagementPage>(
    "/college-admin/student-administration/students/promotion/promote-eligible",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

function buildStudentStatusQuery(params?: StudentStatusManagementPageQuery) {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.selected_request_id) searchParams.set("selected_request_id", params.selected_request_id);
  const suffix = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return suffix;
}

export function fetchStudentStatusManagementPage(params?: StudentStatusManagementPageQuery) {
  return apiRequest<StudentStatusManagementPage>(
    `/college-admin/student-administration/students/status/page${buildStudentStatusQuery(params)}`,
  );
}

export function submitStudentStatusChange(payload: StudentStatusChangeSubmitPayload) {
  return apiRequest<StudentStatusManagementPage>(
    "/college-admin/student-administration/students/status/submit",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function approveStudentStatusChange(payload: StudentStatusApprovePayload) {
  return apiRequest<StudentStatusManagementPage>(
    "/college-admin/student-administration/students/status/approve",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

function buildStudentWithdrawalQuery(params?: StudentWithdrawalPageQuery) {
  const searchParams = new URLSearchParams();
  if (params?.record_id) searchParams.set("record_id", params.record_id);
  if (params?.request_id) searchParams.set("request_id", params.request_id);
  const suffix = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return suffix;
}

export function fetchStudentWithdrawalDiscontinuationPage(params?: StudentWithdrawalPageQuery) {
  return apiRequest<StudentWithdrawalDiscontinuationPage>(
    `/college-admin/student-administration/students/withdrawal/page${buildStudentWithdrawalQuery(params)}`,
  );
}

export function saveStudentWithdrawalDraft(payload: StudentWithdrawalSavePayload) {
  return apiRequest<StudentWithdrawalDiscontinuationPage>(
    "/college-admin/student-administration/students/withdrawal/save",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function submitStudentWithdrawalForApproval(payload: StudentWithdrawalSubmitPayload) {
  return apiRequest<StudentWithdrawalDiscontinuationPage>(
    "/college-admin/student-administration/students/withdrawal/submit",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function cancelStudentWithdrawalDraft(requestId: string) {
  return apiRequest<void>(`/college-admin/student-administration/students/withdrawal/${requestId}`, {
    method: "DELETE",
  });
}

function buildStudentIdCardQuery(params?: StudentIdCardManagementPageQuery) {
  const searchParams = new URLSearchParams();
  if (params?.page && params.page > 1) searchParams.set("page", String(params.page));
  const suffix = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return suffix;
}

export function fetchStudentIdCardManagementPage(params?: StudentIdCardManagementPageQuery) {
  return apiRequest<StudentIdCardManagementPage>(
    `/college-admin/student-administration/students/id-cards/page${buildStudentIdCardQuery(params)}`,
  );
}

export function issueStudentIdCard(payload: StudentIdCardIssuePayload) {
  return apiRequest<StudentIdCardManagementPage>(
    "/college-admin/student-administration/students/id-cards/issue",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function bulkPrintStudentIdCards(payload: StudentIdCardBulkPrintPayload) {
  return apiRequest<StudentIdCardManagementPage>(
    "/college-admin/student-administration/students/id-cards/bulk-print",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function fetchAllStudentsListPage(params: {
  page?: number;
  search?: string;
  programme_code?: string;
  study_year?: string;
  section_code?: string;
  status_filter?: string;
} = {}): Promise<AllStudentsListPage> {
  const searchParams = new URLSearchParams();
  if (params.page && params.page > 1) searchParams.set("page", String(params.page));
  if (params.search) searchParams.set("search", params.search);
  if (params.programme_code) searchParams.set("programme_code", params.programme_code);
  if (params.study_year) searchParams.set("study_year", params.study_year);
  if (params.section_code) searchParams.set("section_code", params.section_code);
  if (params.status_filter) searchParams.set("status_filter", params.status_filter);
  const suffix = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return apiRequest<AllStudentsListPage>(`/college-admin/student-administration/students/list/page${suffix}`);
}