import { apiRequest } from "@/lib/api/client";

import type {
  AssignBatchResult,
  FeeAssessmentBulkAssignPayload,
  FeeAssessmentCreatePayload,
  FeeAssessmentGroupAssignPayload,
  StudentFeeAssignPage,
} from "@/features/college-admin/types/student-fee-assign";

export function fetchStudentFeeAssignPage() {
  return apiRequest<StudentFeeAssignPage>("/college-admin/finance-administration/assessments/assign/page");
}

export function createFeeAssessment(payload: FeeAssessmentCreatePayload) {
  return apiRequest<Record<string, unknown>>("/college-admin/finance-administration/assessments", {
    method: "POST",
    body: payload,
  });
}

export function assignFeeAssessmentsGroup(payload: FeeAssessmentGroupAssignPayload) {
  return apiRequest<AssignBatchResult>("/college-admin/finance-administration/assessments/assign/group", {
    method: "POST",
    body: payload,
  });
}

export function assignFeeAssessmentsBulk(payload: FeeAssessmentBulkAssignPayload) {
  return apiRequest<AssignBatchResult>("/college-admin/finance-administration/assessments/assign/bulk", {
    method: "POST",
    body: payload,
  });
}