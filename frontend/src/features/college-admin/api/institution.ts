import { apiRequest } from "@/lib/api/client";

import type {
  Campus,
  CampusCreate,
  CampusUpdate,
  ConfigurationHistoryItem,
  ConfigurationHistoryPage,
  InstitutionalOverview,
  InstitutionProfile,
  AcademicInstitutionFormValues,
  AcademicInstitutionSettingsPage,
  AcademicYearConfigurationPage,
  AcademicYearSemesterForm,
  CampusContactPage,
  CampusContactPageSave,
  CampusDetailPage,
  CampusManagementDashboard,
  InstitutionBrandingPage,
  InstitutionCalendarFormValues,
  InstitutionCalendarSettingsPage,
  InstitutionPoliciesPage,
  InstitutionInformationPage,
  InstitutionProfilePage,
  InstitutionProfileUpdate,
  InstitutionSettings,
  InstitutionSettingsPatch,
} from "@/features/college-admin/types/institution";

export async function fetchInstitutionalOverview(): Promise<InstitutionalOverview> {
  return apiRequest<InstitutionalOverview>("/college-admin/institution/overview");
}

export async function fetchInstitutionProfile(): Promise<InstitutionProfile> {
  return apiRequest<InstitutionProfile>("/college-admin/institution/profile");
}

export async function updateInstitutionProfile(
  payload: InstitutionProfileUpdate,
): Promise<InstitutionProfile> {
  return apiRequest<InstitutionProfile>("/college-admin/institution/profile", {
    method: "PATCH",
    body: payload,
  });
}

export async function fetchInstitutionProfilePage(): Promise<InstitutionProfilePage> {
  return apiRequest<InstitutionProfilePage>("/college-admin/institution/profile/page");
}

export async function fetchInstitutionInformationPage(): Promise<InstitutionInformationPage> {
  return apiRequest<InstitutionInformationPage>("/college-admin/institution/information/page");
}

export async function saveInstitutionInformationDraft(
  values: Record<string, unknown>,
): Promise<InstitutionInformationPage> {
  return apiRequest<InstitutionInformationPage>("/college-admin/institution/information/draft", {
    method: "PUT",
    body: { values },
  });
}

export async function publishInstitutionInformation(
  values: Record<string, unknown>,
): Promise<InstitutionInformationPage> {
  return apiRequest<InstitutionInformationPage>("/college-admin/institution/information/save", {
    method: "POST",
    body: { values },
  });
}

export async function fetchInstitutionBrandingPage(): Promise<InstitutionBrandingPage> {
  return apiRequest<InstitutionBrandingPage>("/college-admin/institution/branding/page");
}

export async function saveInstitutionBrandingDraft(
  values: Record<string, unknown>,
): Promise<InstitutionBrandingPage> {
  return apiRequest<InstitutionBrandingPage>("/college-admin/institution/branding/draft", {
    method: "PUT",
    body: { values },
  });
}

export async function publishInstitutionBranding(
  values: Record<string, unknown>,
): Promise<InstitutionBrandingPage> {
  return apiRequest<InstitutionBrandingPage>("/college-admin/institution/branding/publish", {
    method: "POST",
    body: { values },
  });
}

export async function uploadBrandingAsset(
  assetKey: string,
  file: File,
): Promise<{ asset_key: string; file_id: string | null; file_name: string | null; uploaded_at: string | null }> {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest(`/college-admin/institution/branding/assets/${encodeURIComponent(assetKey)}`, {
    method: "POST",
    rawBody: formData,
  });
}

export async function fetchCampuses(activeOnly = false): Promise<Campus[]> {
  const suffix = activeOnly ? "?active_only=true" : "";
  return apiRequest<Campus[]>(`/college-admin/institution/campuses${suffix}`);
}
export type InstitutionPoliciesQuery = {
  search?: string;
  category?: string;
  audience?: string;
  status?: string;
  page?: number;
  page_size?: number;
  selected_policy_id?: string;
};

export async function fetchAcademicYearConfigurationPage(
  selectedYearId?: string,
): Promise<AcademicYearConfigurationPage> {
  const qs = selectedYearId
    ? `?selected_year_id=${encodeURIComponent(selectedYearId)}`
    : "";
  return apiRequest<AcademicYearConfigurationPage>(
    `/college-admin/institution/academic-year/page${qs}`,
  );
}

export async function saveAcademicYearConfiguration(
  yearId: string,
  semesterForm: AcademicYearSemesterForm,
): Promise<AcademicYearConfigurationPage> {
  return apiRequest<AcademicYearConfigurationPage>(
    `/college-admin/institution/academic-year/${encodeURIComponent(yearId)}/configuration`,
    { method: "PUT", body: { semester_form: semesterForm } },
  );
}

export async function copyAcademicYearFromPrevious(): Promise<AcademicYearConfigurationPage> {
  return apiRequest<AcademicYearConfigurationPage>(
    "/college-admin/institution/academic-year/copy-previous",
    { method: "POST" },
  );
}

export async function createInstitutionAcademicYear(): Promise<AcademicYearConfigurationPage> {
  return apiRequest<AcademicYearConfigurationPage>(
    "/college-admin/institution/academic-year/new",
    { method: "POST" },
  );
}

export async function fetchInstitutionCalendarSettingsPage(params: {
  page?: number;
  academic_year_id?: string;
} = {}): Promise<InstitutionCalendarSettingsPage> {
  const qs = new URLSearchParams();
  if (params.page) qs.set("page", String(params.page));
  if (params.academic_year_id) qs.set("academic_year_id", params.academic_year_id);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiRequest<InstitutionCalendarSettingsPage>(`/college-admin/institution/calendar/page${suffix}`);
}

export async function saveInstitutionCalendarSettingsPage(payload: {
  form: InstitutionCalendarFormValues;
  page?: number;
  academic_year_id?: string | null;
}): Promise<InstitutionCalendarSettingsPage> {
  return apiRequest<InstitutionCalendarSettingsPage>("/college-admin/institution/calendar/page", {
    method: "PUT",
    body: payload,
  });
}

export async function importInstitutionCalendarHolidays(): Promise<InstitutionCalendarSettingsPage> {
  return apiRequest<InstitutionCalendarSettingsPage>("/college-admin/institution/calendar/import-holidays", {
    method: "POST",
  });
}

export async function fetchInstitutionPoliciesPage(
  params: InstitutionPoliciesQuery = {},
): Promise<InstitutionPoliciesPage> {
  const qs = new URLSearchParams();
  if (params.search) qs.set("search", params.search);
  if (params.category) qs.set("category", params.category);
  if (params.audience) qs.set("audience", params.audience);
  if (params.status) qs.set("status", params.status);
  if (params.page) qs.set("page", String(params.page));
  if (params.page_size) qs.set("page_size", String(params.page_size));
  if (params.selected_policy_id) qs.set("selected_policy_id", params.selected_policy_id);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiRequest<InstitutionPoliciesPage>(`/college-admin/institution/policies/page${suffix}`);
}

export async function fetchAcademicInstitutionSettingsPage(): Promise<AcademicInstitutionSettingsPage> {
  return apiRequest<AcademicInstitutionSettingsPage>(
    "/college-admin/institution/academic-settings/page",
  );
}

export async function saveAcademicInstitutionSettingsPage(
  form: AcademicInstitutionFormValues,
): Promise<AcademicInstitutionSettingsPage> {
  return apiRequest<AcademicInstitutionSettingsPage>(
    "/college-admin/institution/academic-settings/page",
    { method: "PUT", body: { form } },
  );
}

export async function resetAcademicInstitutionSettingsPage(): Promise<AcademicInstitutionSettingsPage> {
  return apiRequest<AcademicInstitutionSettingsPage>(
    "/college-admin/institution/academic-settings/reset",
    { method: "POST" },
  );
}

export async function fetchCampusManagementDashboard(): Promise<CampusManagementDashboard> {
  return apiRequest<CampusManagementDashboard>("/college-admin/institution/campuses/dashboard");
}

export async function fetchCampusDetailPage(campusId: string): Promise<CampusDetailPage> {
  return apiRequest<CampusDetailPage>(
    `/college-admin/institution/campuses/${encodeURIComponent(campusId)}/page`,
  );
}

export async function fetchCampusContactPage(campusId: string): Promise<CampusContactPage> {
  return apiRequest<CampusContactPage>(
    `/college-admin/institution/campuses/${encodeURIComponent(campusId)}/contact/page`,
  );
}

export async function saveCampusContactPage(
  campusId: string,
  payload: CampusContactPageSave,
): Promise<CampusContactPage> {
  return apiRequest<CampusContactPage>(
    `/college-admin/institution/campuses/${encodeURIComponent(campusId)}/contact/page`,
    { method: "PUT", body: payload },
  );
}


export async function fetchCampus(campusId: string): Promise<Campus> {
  return apiRequest<Campus>(
    `/college-admin/institution/campuses/${encodeURIComponent(campusId)}`,
  );
}

export async function createCampus(payload: CampusCreate): Promise<Campus> {
  return apiRequest<Campus>("/college-admin/institution/campuses", {
    method: "POST",
    body: payload,
  });
}

export async function updateCampus(
  campusId: string,
  payload: CampusUpdate,
): Promise<Campus> {
  return apiRequest<Campus>(
    `/college-admin/institution/campuses/${encodeURIComponent(campusId)}`,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export async function fetchInstitutionSettings(): Promise<InstitutionSettings> {
  return apiRequest<InstitutionSettings>(
    "/college-admin/institution/settings",
  );
}

export async function updateInstitutionSettings(
  payload: InstitutionSettingsPatch,
): Promise<InstitutionSettings> {
  return apiRequest<InstitutionSettings>(
    "/college-admin/institution/settings",
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export async function fetchConfigurationHistory(): Promise<
  ConfigurationHistoryItem[]
> {
  return apiRequest<ConfigurationHistoryItem[]>(
    "/college-admin/institution/configuration-history",
  );
}

export type ConfigurationHistoryPageQuery = {
  page?: number;
  date_range?: string;
  setting_area?: string;
  actor_id?: string;
  search?: string;
  selected_change_id?: string;
};

export async function fetchConfigurationHistoryPage(
  params: ConfigurationHistoryPageQuery = {},
): Promise<ConfigurationHistoryPage> {
  const qs = new URLSearchParams();
  if (params.page) qs.set("page", String(params.page));
  if (params.date_range) qs.set("date_range", params.date_range);
  if (params.setting_area) qs.set("setting_area", params.setting_area);
  if (params.actor_id) qs.set("actor_id", params.actor_id);
  if (params.search) qs.set("search", params.search);
  if (params.selected_change_id) qs.set("selected_change_id", params.selected_change_id);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiRequest<ConfigurationHistoryPage>(
    `/college-admin/institution/configuration-history/page${suffix}`,
  );
}