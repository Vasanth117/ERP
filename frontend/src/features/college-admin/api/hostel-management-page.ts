import { apiRequest } from "@/lib/api/client";

import type { HostelManagementPage, HostelManagementPageQuery } from "@/features/college-admin/types/hostel-management-page";

export function fetchHostelManagementPage(screenSlug: string, params?: HostelManagementPageQuery) {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  const suffix = qs.size ? `?${qs.toString()}` : "";
  return apiRequest<HostelManagementPage>(
    `/college-admin/hostel-administration/screens/${encodeURIComponent(screenSlug)}/management/page${suffix}`,
  );
}