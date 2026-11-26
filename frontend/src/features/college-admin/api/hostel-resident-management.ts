import { apiRequest } from "@/lib/api/client";

import type {
  HostelResidentManagementPage,
  HostelResidentManagementPageQuery,
} from "@/features/college-admin/types/hostel-resident-management";

export function fetchHostelResidentManagementPage(params?: HostelResidentManagementPageQuery) {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  if (params?.search) qs.set("search", params.search);
  if (params?.block_code) qs.set("block_code", params.block_code);
  if (params?.status_filter) qs.set("status_filter", params.status_filter);
  const suffix = qs.size ? `?${qs.toString()}` : "";
  return apiRequest<HostelResidentManagementPage>(
    `/college-admin/hostel-administration/residents/management/page${suffix}`,
  );
}