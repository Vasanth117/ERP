import { apiRequest } from "@/lib/api/client";

import type {
  HostelBuildingManagementPage,
  HostelBuildingManagementPageQuery,
} from "@/features/college-admin/types/hostel-building-management";

export function fetchHostelBuildingManagementPage(params?: HostelBuildingManagementPageQuery) {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  const suffix = qs.size ? `?${qs.toString()}` : "";
  return apiRequest<HostelBuildingManagementPage>(
    `/college-admin/hostel-administration/buildings/management/page${suffix}`,
  );
}