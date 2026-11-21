import { apiRequest } from "@/lib/api/client";
import type { AcademicConfigurationDashboardPage } from "@/features/college-admin/types/academic-configuration-dashboard";
import type {
  AcademicYearManagementCreatePayload,
  AcademicYearManagementPage,
  AcademicYearManagementRulesPayload,
} from "@/features/college-admin/types/academic-year-management";
import type {
  ProgrammeManagementCreatePayload,
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

export function createAcademicYearManagement(payload: AcademicYearManagementCreatePayload) {
  return apiRequest<AcademicYearManagementPage>("/college-admin/academic-config/years/management/create", {
    method: "POST",
    body: JSON.stringify({
      ...payload,
      copy_from_year_id: payload.copy_from_year_id || null,
      start_date: payload.start_date || null,
      end_date: payload.end_date || null,
      admission_intake_opens: payload.admission_intake_opens || null,
    }),
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
  return apiRequest<ProgrammeManagementPage>("/college-admin/academic-config/programmes/management/create", {
    method: "POST",
    body: JSON.stringify({
      ...payload,
      department_id: payload.department_id || null,
    }),
  });
}