import { apiRequest } from "@/lib/api/client";

import type {
  HostelVisitorManagementPage,
  HostelVisitorManagementPageQuery,
} from "@/features/college-admin/types/hostel-visitor-management";

export function fetchHostelVisitorManagementPage(params?: HostelVisitorManagementPageQuery) {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  const suffix = qs.size ? `?${qs.toString()}` : "";
  return apiRequest<HostelVisitorManagementPage>(
    `/college-admin/hostel-administration/visitors/management/page${suffix}`,
  );
}