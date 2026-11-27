import { apiRequest } from "@/lib/api/client";

import type {
  ExaminationConfigurationPage,
  ExaminationConfigurationPageQuery,
  ExaminationConfigurationSavePayload,
} from "@/features/college-admin/types/examination-configuration";
import type {
  ExaminationDashboardPage,
  ExaminationDashboardPageQuery,
} from "@/features/college-admin/types/examination-dashboard";
import type {
  ExamTimetableManagementActionPayload,
  ExamTimetableManagementPage,
  ExamTimetableManagementPageQuery,
} from "@/features/college-admin/types/exam-timetable-management";
import type {
  ExaminationSessionManagementPage,
  ExaminationSessionManagementPageQuery,
} from "@/features/college-admin/types/examination-session-management";
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
  if (params?.search) search.set("search", params.search);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchExaminationDashboardPage(params?: ExaminationDashboardPageQuery) {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  const qs = search.toString();
  return apiRequest<ExaminationDashboardPage>(
    `/college-admin/examination-administration/dashboard/page${qs ? `?${qs}` : ""}`,
  );
}

export function fetchExamRegistrationManagementPage(params?: ExamRegistrationManagementPageQuery) {
  return apiRequest<ExamRegistrationManagementPage>(
    `/college-admin/examination-administration/registrations/page${buildQuery(params)}`,
  );
}

export function fetchExaminationSessionManagementPage(params?: ExaminationSessionManagementPageQuery) {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  const qs = search.toString();
  return apiRequest<ExaminationSessionManagementPage>(
    `/college-admin/examination-administration/sessions/page${qs ? `?${qs}` : ""}`,
  );
}

function configurationQuery(params?: ExaminationConfigurationPageQuery): string {
  const search = new URLSearchParams();
  if (params?.session_id) search.set("session_id", params.session_id);
  if (params?.mode) search.set("mode", params.mode);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchExaminationConfigurationPage(params?: ExaminationConfigurationPageQuery) {
  return apiRequest<ExaminationConfigurationPage>(
    `/college-admin/examination-administration/sessions/setup/page${configurationQuery(params)}`,
  );
}

function timetableQuery(params?: ExamTimetableManagementPageQuery): string {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.session_id) search.set("session_id", params.session_id);
  if (params?.programme_code) search.set("programme_code", params.programme_code);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchExamTimetableManagementPage(params?: ExamTimetableManagementPageQuery) {
  return apiRequest<ExamTimetableManagementPage>(
    `/college-admin/examination-administration/timetable/page${timetableQuery(params)}`,
  );
}

export function regenerateExamTimetable(payload: ExamTimetableManagementActionPayload) {
  return apiRequest<ExamTimetableManagementPage>(
    "/college-admin/examination-administration/timetable/regenerate",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function publishExamTimetable(payload: ExamTimetableManagementActionPayload) {
  return apiRequest<ExamTimetableManagementPage>(
    "/college-admin/examination-administration/timetable/publish",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function saveExaminationConfiguration(payload: ExaminationConfigurationSavePayload) {
  return apiRequest<ExaminationConfigurationPage>(
    "/college-admin/examination-administration/sessions/setup/save",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function fetchStudentExamEligibilityPage(params?: { page?: number; session_id?: string }) {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.session_id) search.set("session_id", params.session_id);
  const qs = search.toString();
  return apiRequest<import("@/features/college-admin/types/student-exam-eligibility").StudentExamEligibilityPage>(
    `/college-admin/examination-administration/eligibility/students/page${qs ? `?${qs}` : ""}`,
  );
}

export function rerunStudentExamEligibility(payload: { session_id: string; page?: number }) {
  return apiRequest<import("@/features/college-admin/types/student-exam-eligibility").StudentExamEligibilityPage>(
    "/college-admin/examination-administration/eligibility/students/rerun",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function fetchHallTicketAdministrationPage(params?: { page?: number; session_id?: string }) {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.session_id) search.set("session_id", params.session_id);
  const qs = search.toString();
  return apiRequest<import("@/features/college-admin/types/hall-ticket-administration").HallTicketAdministrationPage>(
    `/college-admin/examination-administration/hall-tickets/page${qs ? `?${qs}` : ""}`,
  );
}

export function generateAllHallTickets(payload: { session_id: string; page?: number }) {
  return apiRequest<import("@/features/college-admin/types/hall-ticket-administration").HallTicketAdministrationPage>(
    "/college-admin/examination-administration/hall-tickets/generate-all",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function releaseHallTickets(payload: { session_id: string; page?: number }) {
  return apiRequest<import("@/features/college-admin/types/hall-ticket-administration").HallTicketAdministrationPage>(
    "/college-admin/examination-administration/hall-tickets/release",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function fetchExaminationHallSeatingManagementPage(params?: {
  page?: number;
  session_id?: string;
}) {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.session_id) search.set("session_id", params.session_id);
  const qs = search.toString();
  return apiRequest<
    import("@/features/college-admin/types/examination-hall-seating-management").ExaminationHallSeatingManagementPage
  >(`/college-admin/examination-administration/halls-seating/page${qs ? `?${qs}` : ""}`);
}

export function autoAllocateHallSeating(payload: { session_id: string; page?: number }) {
  return apiRequest<
    import("@/features/college-admin/types/examination-hall-seating-management").ExaminationHallSeatingManagementPage
  >("/college-admin/examination-administration/halls-seating/auto-allocate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function confirmHallSeating(payload: { session_id: string; page?: number }) {
  return apiRequest<
    import("@/features/college-admin/types/examination-hall-seating-management").ExaminationHallSeatingManagementPage
  >("/college-admin/examination-administration/halls-seating/confirm", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchInvigilatorAllocationPage(params?: { page?: number; session_id?: string }) {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.session_id) search.set("session_id", params.session_id);
  const qs = search.toString();
  return apiRequest<import("@/features/college-admin/types/invigilator-allocation").InvigilatorAllocationPage>(
    `/college-admin/examination-administration/invigilation/page${qs ? `?${qs}` : ""}`,
  );
}

export function autoAssignInvigilators(payload: { session_id: string; page?: number }) {
  return apiRequest<import("@/features/college-admin/types/invigilator-allocation").InvigilatorAllocationPage>(
    "/college-admin/examination-administration/invigilation/auto-assign",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function publishInvigilatorRoster(payload: { session_id: string; page?: number }) {
  return apiRequest<import("@/features/college-admin/types/invigilator-allocation").InvigilatorAllocationPage>(
    "/college-admin/examination-administration/invigilation/publish-roster",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function fetchMarksEntryManagementPage(params?: { page?: number; session_id?: string }) {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.session_id) search.set("session_id", params.session_id);
  const qs = search.toString();
  return apiRequest<import("@/features/college-admin/types/marks-entry-management").MarksEntryManagementPage>(
    `/college-admin/examination-administration/marks-entry/page${qs ? `?${qs}` : ""}`,
  );
}

export function sendMarksEntryReminders(payload: { session_id: string; page?: number }) {
  return apiRequest<import("@/features/college-admin/types/marks-entry-management").MarksEntryManagementPage>(
    "/college-admin/examination-administration/marks-entry/send-reminders",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function lockMarksEntry(payload: { session_id: string; page?: number }) {
  return apiRequest<import("@/features/college-admin/types/marks-entry-management").MarksEntryManagementPage>(
    "/college-admin/examination-administration/marks-entry/lock",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function fetchInternalExternalAssessmentPage(params?: { session_id?: string }) {
  const search = new URLSearchParams();
  if (params?.session_id) search.set("session_id", params.session_id);
  const qs = search.toString();
  return apiRequest<import("@/features/college-admin/types/internal-external-assessment").InternalExternalAssessmentPage>(
    `/college-admin/examination-administration/assessment-pattern/page${qs ? `?${qs}` : ""}`,
  );
}

export function saveInternalExternalAssessment(
  payload: import("@/features/college-admin/types/internal-external-assessment").InternalExternalAssessmentSavePayload,
) {
  return apiRequest<import("@/features/college-admin/types/internal-external-assessment").InternalExternalAssessmentPage>(
    "/college-admin/examination-administration/assessment-pattern/save",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function createInternalExternalAssessmentPattern(sessionId: string) {
  return apiRequest<import("@/features/college-admin/types/internal-external-assessment").InternalExternalAssessmentPage>(
    "/college-admin/examination-administration/assessment-pattern/create",
    { method: "POST", body: JSON.stringify({ session_id: sessionId }) },
  );
}

export function fetchResultProcessingPage(params?: { session_id?: string }) {
  const search = new URLSearchParams();
  if (params?.session_id) search.set("session_id", params.session_id);
  const qs = search.toString();
  return apiRequest<import("@/features/college-admin/types/result-processing").ResultProcessingPage>(
    `/college-admin/examination-administration/results/processing/page${qs ? `?${qs}` : ""}`,
  );
}

export function processResults(payload: { session_id: string }) {
  return apiRequest<import("@/features/college-admin/types/result-processing").ResultProcessingPage>(
    "/college-admin/examination-administration/results/processing/process",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function fetchResultApprovalPage(params?: { page?: number; session_id?: string }) {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.session_id) search.set("session_id", params.session_id);
  const qs = search.toString();
  return apiRequest<import("@/features/college-admin/types/result-approval").ResultApprovalPage>(
    `/college-admin/examination-administration/results/approval/page${qs ? `?${qs}` : ""}`,
  );
}

export function approveResultApproval(payload: { session_id: string; page?: number }) {
  return apiRequest<import("@/features/college-admin/types/result-approval").ResultApprovalPage>(
    "/college-admin/examination-administration/results/approval/approve",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function returnResultApproval(payload: { session_id: string; page?: number }) {
  return apiRequest<import("@/features/college-admin/types/result-approval").ResultApprovalPage>(
    "/college-admin/examination-administration/results/approval/return",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function fetchResultPublicationPage(params?: { page?: number; session_id?: string }) {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.session_id) search.set("session_id", params.session_id);
  const qs = search.toString();
  return apiRequest<import("@/features/college-admin/types/result-publication").ResultPublicationPage>(
    `/college-admin/examination-administration/results/publication/page${qs ? `?${qs}` : ""}`,
  );
}

export function publishResultsNow(payload: { session_id: string; page?: number }) {
  return apiRequest<import("@/features/college-admin/types/result-publication").ResultPublicationPage>(
    "/college-admin/examination-administration/results/publication/publish-now",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function scheduleResultPublication(payload: { session_id: string; page?: number; publish_at?: string }) {
  return apiRequest<import("@/features/college-admin/types/result-publication").ResultPublicationPage>(
    "/college-admin/examination-administration/results/publication/schedule",
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function fetchRevaluationManagementPage(params?: { page?: number; session_id?: string }) {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.session_id) search.set("session_id", params.session_id);
  const qs = search.toString();
  return apiRequest<import("@/features/college-admin/types/revaluation-management").RevaluationManagementPage>(
    `/college-admin/examination-administration/revaluation/page${qs ? `?${qs}` : ""}`,
  );
}

export function fetchSupplementaryExaminationManagementPage(params?: { page?: number; session_id?: string }) {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.session_id) search.set("session_id", params.session_id);
  const qs = search.toString();
  return apiRequest<import("@/features/college-admin/types/supplementary-examination-management").SupplementaryExaminationManagementPage>(
    `/college-admin/examination-administration/supplementary/page${qs ? `?${qs}` : ""}`,
  );
}

export function createSupplementaryExaminationSession(payload: { session_id?: string; page?: number }) {
  return apiRequest<import("@/features/college-admin/types/supplementary-examination-management").SupplementaryExaminationManagementPage>(
    "/college-admin/examination-administration/supplementary/create-session",
    { method: "POST", body: JSON.stringify(payload) },
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