import { apiRequest } from "@/lib/api/client";

import type {
  HostelFeeManagementPage,
  HostelFeeManagementPageQuery,
} from "@/features/college-admin/types/hostel-fee-management";

export function fetchHostelFeeManagementPage(params?: HostelFeeManagementPageQuery) {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  const suffix = qs.size ? `?${qs.toString()}` : "";
  return apiRequest<HostelFeeManagementPage>(
    `/college-admin/hostel-administration/fees/management/page${suffix}`,
  );
}