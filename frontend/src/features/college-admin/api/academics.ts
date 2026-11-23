import { apiRequest } from "@/lib/api/client";
import type { AcademicConfigurationDashboardPage } from "@/features/college-admin/types/academic-configuration-dashboard";
import type { AcademicYearDetailsPage } from "@/features/college-admin/types/academic-year-details";
import type {
  AcademicYearManagementCreatePayload,
  AcademicYearManagementPage,
  AcademicYearManagementRulesPayload,
} from "@/features/college-admin/types/academic-year-management";
import type {
  AcademicYearWizardDraftPayload,
  NewAcademicYearWizardPage,
  NewAcademicYearWizardSaveResult,
} from "@/features/college-admin/types/new-academic-year-wizard";
import type {
  CourseConfigurationPage,
  CourseConfigurationSavePayload,
  CurriculumManagementPage,
  SubjectManagementPage,
} from "@/features/college-admin/types/course-curriculum";
import type {
  CreditConfigurationPage,
  CreditConfigurationSavePayload,
  GradingSystemConfigurationPage,
  GradingSystemConfigurationSavePayload,
} from "@/features/college-admin/types/credit-grading";
import type {
  AcademicCalendarAddEventPayload,
  AcademicCalendarConfigurationPage,
  AcademicCalendarPublishPayload,
} from "@/features/college-admin/types/academic-calendar-configuration";
import type {
  BatchSectionAddSectionPayload,
  BatchSectionAllocationRulesPayload,
  BatchSectionAutoAllocatePayload,
  BatchSectionConfigurationPage,
} from "@/features/college-admin/types/batch-section-configuration";
import type { ConfigurationHistoryPage } from "@/features/college-admin/types/institution";
import type {
  RegulationManagementCreatePayload,
  RegulationManagementPage,
} from "@/features/college-admin/types/regulation-management";
import type { ProgrammeDetailsPage } from "@/features/college-admin/types/programme-details";
import type {
  ProgrammeManagementCreatePayload,
  ProgrammeManagementCreateResult,
  ProgrammeManagementPage,
} from "@/features/college-admin/types/programme-management";
import type {
  SemesterCreatePayload,
  SemesterManagementPage,
  SemesterSettingsSavePayload,
} from "@/features/college-admin/types/semester-management";

export type AcademicYear = {
  year_id: string;
  label: string;
  status?: string;
  is_current?: boolean;
};

export type AcademicTerm = {
  term_id: string;
  label: string;
  academic_year_id?: string;
  is_current?: boolean;
};

export type Programme = {
  programme_id: string;
  name: string;
  code?: string;
  department_id?: string;
};

export function fetchAcademicYears() {
  return apiRequest<AcademicYear[]>("/college-admin/academic-config/years");
}

export function fetchAcademicTerms(yearId?: string) {
  const q = yearId ? `?academic_year_id=${encodeURIComponent(yearId)}` : "";
  return apiRequest<AcademicTerm[]>(`/college-admin/academic-config/terms${q}`);
}

export function fetchProgrammes() {
  return apiRequest<Programme[]>("/college-admin/academic-config/programmes");
}

export function fetchConfigHistory() {
  return apiRequest<unknown[]>("/college-admin/academic-config/configuration-history");
}

export function fetchAcademicConfigurationDashboardPage() {
  return apiRequest<AcademicConfigurationDashboardPage>(
    "/college-admin/academic-config/configuration-dashboard/page",
  );
}

export function fetchAcademicYearManagementPage(page = 1) {
  const q = page > 1 ? `?page=${page}` : "";
  return apiRequest<AcademicYearManagementPage>(`/college-admin/academic-config/years/management/page${q}`);
}

export function fetchNewAcademicYearWizardPage(draftId?: string) {
  const q = draftId ? `?draft_id=${encodeURIComponent(draftId)}` : "";
  return apiRequest<NewAcademicYearWizardPage>(`/college-admin/academic-config/years/management/create-wizard/page${q}`);
}

export function saveAcademicYearWizardDraft(payload: AcademicYearWizardDraftPayload) {
  return apiRequest<NewAcademicYearWizardSaveResult>("/college-admin/academic-config/years/management/create-wizard/draft", {
    method: "POST",
    body: payload,
  });
}

export function fetchAcademicYearDetailsPage(yearId: string) {
  return apiRequest<AcademicYearDetailsPage>(
    `/college-admin/academic-config/years/management/details/page?year_id=${encodeURIComponent(yearId)}`,
  );
}

export function createAcademicYearManagement(payload: AcademicYearManagementCreatePayload) {
  return apiRequest<AcademicYearManagementPage>("/college-admin/academic-config/years/management/create", {
    method: "POST",
    body: {
      ...payload,
      copy_from_year_id: payload.copy_from_year_id || null,
      start_date: payload.start_date || null,
      end_date: payload.end_date || null,
      admission_intake_opens: payload.admission_intake_opens || null,
    },
  });
}

export function closeCurrentAcademicYear() {
  return apiRequest<AcademicYearManagementPage>("/college-admin/academic-config/years/management/close-current", {
    method: "POST",
  });
}

export function saveAcademicYearManagementRules(payload: AcademicYearManagementRulesPayload) {
  return apiRequest<AcademicYearManagementPage>("/college-admin/academic-config/years/management/rules", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function fetchSemesterManagementPage(params?: {
  academic_year_id?: string;
  term_id?: string;
}) {
  const search = new URLSearchParams();
  if (params?.academic_year_id) search.set("academic_year_id", params.academic_year_id);
  if (params?.term_id) search.set("term_id", params.term_id);
  const q = search.toString();
  return apiRequest<SemesterManagementPage>(
    `/college-admin/academic-config/semesters/management/page${q ? `?${q}` : ""}`,
  );
}

export function saveSemesterManagementSettings(payload: SemesterSettingsSavePayload) {
  return apiRequest<SemesterManagementPage>("/college-admin/academic-config/semesters/management/settings", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function createSemesterManagementTerm(payload: SemesterCreatePayload) {
  return apiRequest<SemesterManagementPage>("/college-admin/academic-config/semesters/management/create", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchProgrammeManagementPage(params?: {
  page?: number;
  search?: string;
  level_filter?: string;
  department_id?: string;
  regulation_filter?: string;
  status_filter?: string;
}) {
  const search = new URLSearchParams();
  if (params?.page && params.page > 1) search.set("page", String(params.page));
  if (params?.search) search.set("search", params.search);
  if (params?.level_filter) search.set("level_filter", params.level_filter);
  if (params?.department_id) search.set("department_id", params.department_id);
  if (params?.regulation_filter) search.set("regulation_filter", params.regulation_filter);
  if (params?.status_filter) search.set("status_filter", params.status_filter);
  const q = search.toString();
  return apiRequest<ProgrammeManagementPage>(
    `/college-admin/academic-config/programmes/management/page${q ? `?${q}` : ""}`,
  );
}

export function createProgrammeManagement(payload: ProgrammeManagementCreatePayload) {
  return apiRequest<ProgrammeManagementCreateResult>("/college-admin/academic-config/programmes/management/create", {
    method: "POST",
    body: {
      ...payload,
      department_id: payload.department_id || null,
      programme_level: payload.programme_level || null,
      regulation_code: payload.regulation_code || null,
      short_name: payload.short_name || null,
      description: payload.description || null,
      entry_qualification: payload.entry_qualification || null,
      approved_intake: payload.approved_intake ?? null,
    },
  });
}

export function fetchProgrammeDetailsPage(programmeId: string) {
  const q = new URLSearchParams({ programme_id: programmeId });
  return apiRequest<ProgrammeDetailsPage>(
    `/college-admin/academic-config/programmes/details/page?${q.toString()}`,
  );
}

export function fetchSubjectManagementPage(params?: {
  page?: number;
  search?: string;
  department_id?: string;
  type_filter?: string;
  regulation_filter?: string;
  semester_filter?: string;
}) {
  const search = new URLSearchParams();
  if (params?.page && params.page > 1) search.set("page", String(params.page));
  if (params?.search) search.set("search", params.search);
  if (params?.department_id) search.set("department_id", params.department_id);
  if (params?.type_filter) search.set("type_filter", params.type_filter);
  if (params?.regulation_filter) search.set("regulation_filter", params.regulation_filter);
  if (params?.semester_filter) search.set("semester_filter", params.semester_filter);
  const q = search.toString();
  return apiRequest<SubjectManagementPage>(
    `/college-admin/academic-config/subjects/management/page${q ? `?${q}` : ""}`,
  );
}

export function fetchCurriculumManagementPage(params?: { programme_id?: string; semester?: number }) {
  const search = new URLSearchParams();
  if (params?.programme_id) search.set("programme_id", params.programme_id);
  if (params?.semester) search.set("semester", String(params.semester));
  const q = search.toString();
  return apiRequest<CurriculumManagementPage>(
    `/college-admin/academic-config/curriculum/management/page${q ? `?${q}` : ""}`,
  );
}

export function fetchCourseConfigurationPage(params?: { course_id?: string; mode?: string }) {
  const search = new URLSearchParams();
  if (params?.course_id) search.set("course_id", params.course_id);
  if (params?.mode) search.set("mode", params.mode);
  const q = search.toString();
  return apiRequest<CourseConfigurationPage>(
    `/college-admin/academic-config/courses/configuration/page${q ? `?${q}` : ""}`,
  );
}

export function saveCourseConfiguration(payload: CourseConfigurationSavePayload) {
  return apiRequest<CourseConfigurationPage>("/college-admin/academic-config/courses/configuration/save", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function fetchCreditConfigurationPage() {
  return apiRequest<CreditConfigurationPage>("/college-admin/academic-config/credits/configuration/page");
}

export function saveCreditConfiguration(payload: CreditConfigurationSavePayload) {
  return apiRequest<CreditConfigurationPage>("/college-admin/academic-config/credits/configuration/save", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function resetCreditConfiguration() {
  return apiRequest<CreditConfigurationPage>("/college-admin/academic-config/credits/configuration/reset", {
    method: "POST",
  });
}

export function fetchGradingSystemConfigurationPage() {
  return apiRequest<GradingSystemConfigurationPage>("/college-admin/academic-config/grading/configuration/page");
}

export function saveGradingSystemConfiguration(payload: GradingSystemConfigurationSavePayload) {
  return apiRequest<GradingSystemConfigurationPage>("/college-admin/academic-config/grading/configuration/save", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function fetchRegulationManagementPage(regulation_code?: string) {
  const q = regulation_code ? `?regulation_code=${encodeURIComponent(regulation_code)}` : "";
  return apiRequest<RegulationManagementPage>(`/college-admin/academic-config/regulations/management/page${q}`);
}

export function createRegulationManagement(payload: RegulationManagementCreatePayload) {
  return apiRequest<RegulationManagementPage>("/college-admin/academic-config/regulations/management/create", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

function buildAcademicCalendarQuery(params?: Record<string, string | number | undefined>) {
  if (!params) return "";
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const q = search.toString();
  return q ? `?${q}` : "";
}

export function fetchAcademicCalendarConfigurationPage(params?: Record<string, string | number | undefined>) {
  return apiRequest<AcademicCalendarConfigurationPage>(
    `/college-admin/academic-config/calendars/configuration/page${buildAcademicCalendarQuery(params)}`,
  );
}

export function addAcademicCalendarEvent(payload: AcademicCalendarAddEventPayload) {
  return apiRequest<AcademicCalendarConfigurationPage>("/college-admin/academic-config/calendars/configuration/events", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function publishAcademicCalendarConfiguration(payload: AcademicCalendarPublishPayload) {
  return apiRequest<AcademicCalendarConfigurationPage>("/college-admin/academic-config/calendars/configuration/publish", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

function buildBatchSectionQuery(params?: Record<string, string | number | undefined>) {
  if (!params) return "";
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const q = search.toString();
  return q ? `?${q}` : "";
}

export function fetchBatchSectionConfigurationPage(params?: Record<string, string | number | undefined>) {
  return apiRequest<BatchSectionConfigurationPage>(
    `/college-admin/academic-config/batches/configuration/page${buildBatchSectionQuery(params)}`,
  );
}

export function saveBatchSectionAllocationRules(payload: BatchSectionAllocationRulesPayload) {
  return apiRequest<BatchSectionConfigurationPage>("/college-admin/academic-config/batches/configuration/rules", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function addBatchSection(payload: BatchSectionAddSectionPayload) {
  return apiRequest<BatchSectionConfigurationPage>("/college-admin/academic-config/batches/configuration/sections", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function autoAllocateBatchSections(payload: BatchSectionAutoAllocatePayload) {
  return apiRequest<BatchSectionConfigurationPage>("/college-admin/academic-config/batches/configuration/auto-allocate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type AcademicConfigurationHistoryPageQuery = {
  page?: number;
  date_range?: string;
  setting_area?: string;
  actor_id?: string;
  search?: string;
  selected_change_id?: string;
};

export function fetchAcademicConfigurationHistoryPage(params: AcademicConfigurationHistoryPageQuery = {}) {
  const qs = new URLSearchParams();
  if (params.page) qs.set("page", String(params.page));
  if (params.date_range) qs.set("date_range", params.date_range);
  if (params.setting_area) qs.set("setting_area", params.setting_area);
  if (params.actor_id) qs.set("actor_id", params.actor_id);
  if (params.search) qs.set("search", params.search);
  if (params.selected_change_id) qs.set("selected_change_id", params.selected_change_id);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiRequest<ConfigurationHistoryPage>(`/college-admin/academic-config/configuration-history/page${suffix}`);
}