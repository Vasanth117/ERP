import { apiRequest } from "@/lib/api/client";

import type {
  HostelBedAllocationPage,
  HostelBedAllocationPageQuery,
} from "@/features/college-admin/types/hostel-bed-allocation";

export function fetchHostelBedAllocationPage(params?: HostelBedAllocationPageQuery) {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  if (params?.academic_year_label) qs.set("academic_year_label", params.academic_year_label);
  const suffix = qs.size ? `?${qs.toString()}` : "";
  return apiRequest<HostelBedAllocationPage>(
    `/college-admin/hostel-administration/allocations/management/page${suffix}`,
  );
}