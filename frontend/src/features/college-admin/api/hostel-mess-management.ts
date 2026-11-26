import { apiRequest } from "@/lib/api/client";

import type { HostelMessManagementPage } from "@/features/college-admin/types/hostel-mess-management";

export function fetchHostelMessManagementPage() {
  return apiRequest<HostelMessManagementPage>("/college-admin/hostel-administration/mess/management/page");
}