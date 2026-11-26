import { apiRequest } from "@/lib/api/client";

import type { LibrarySettingsFormValues, LibrarySettingsPage } from "@/features/college-admin/types/library-settings-page";

export function fetchLibrarySettingsPage() {
  return apiRequest<LibrarySettingsPage>("/college-admin/library-administration/settings/management/page");
}

export function saveLibrarySettingsPage(form: LibrarySettingsFormValues) {
  return apiRequest<LibrarySettingsPage>("/college-admin/library-administration/settings/management/page", {
    method: "PUT",
    body: JSON.stringify({ form }),
  });
}