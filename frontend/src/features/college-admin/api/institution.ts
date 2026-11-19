import { apiRequest } from "@/lib/api/client";

import type {
  Campus,
  CampusCreate,
  CampusUpdate,
  ConfigurationHistoryItem,
  InstitutionProfile,
  InstitutionProfileUpdate,
  InstitutionSettings,
  InstitutionSettingsPatch,
} from "@/features/college-admin/types/institution";

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

export async function fetchCampuses(activeOnly = false): Promise<Campus[]> {
  const suffix = activeOnly ? "?active_only=true" : "";
  return apiRequest<Campus[]>(`/college-admin/institution/campuses${suffix}`);
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