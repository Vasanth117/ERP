import { apiRequest } from "@/lib/api/client";

import type { HostelSettingsFormValues, HostelSettingsPage } from "@/features/college-admin/types/hostel-settings-page";

export function fetchHostelSettingsPage() {
  return apiRequest<HostelSettingsPage>("/college-admin/hostel-administration/settings/management/page");
}

export function saveHostelSettingsPage(form: HostelSettingsFormValues) {
  return apiRequest<HostelSettingsPage>("/college-admin/hostel-administration/settings/management/page", {
    method: "PUT",
    body: { form },
  });
}