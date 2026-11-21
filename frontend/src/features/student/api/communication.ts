import { apiRequest } from "@/lib/api/client";

const BASE = "/students";

export type CommunicationPreferences = {
  email_enabled: boolean;
  push_enabled: boolean;
  academic_enabled: boolean;
  finance_enabled: boolean;
  examination_enabled: boolean;
  library_enabled: boolean;
};

export type CommunicationPreferencesUpdate = Partial<CommunicationPreferences>;

export function fetchCommunicationPreferences() {
  return apiRequest<CommunicationPreferences>(`${BASE}/me/communication/preferences`);
}

export function updateCommunicationPreferences(payload: CommunicationPreferencesUpdate) {
  return apiRequest<CommunicationPreferences>(`${BASE}/me/communication/preferences`, {
    method: "PATCH",
    body: payload,
  });
}