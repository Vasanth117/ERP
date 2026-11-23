import { apiRequest } from "@/lib/api/client";

import type { FinanceSettingsFormValues, FinanceSettingsPage } from "@/features/college-admin/types/finance-settings-page";

export function fetchFinanceSettingsPage() {
  return apiRequest<FinanceSettingsPage>("/college-admin/finance-administration/settings/page");
}

export function saveFinanceSettingsPage(form: FinanceSettingsFormValues) {
  return apiRequest<FinanceSettingsPage>("/college-admin/finance-administration/settings/page", {
    method: "PUT",
    body: { form },
  });
}