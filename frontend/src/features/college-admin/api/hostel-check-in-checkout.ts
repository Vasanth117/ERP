import { apiRequest } from "@/lib/api/client";

import type {
  HostelCheckInCheckoutPage,
  HostelCheckInCheckoutPageQuery,
} from "@/features/college-admin/types/hostel-check-in-checkout";

export function fetchHostelCheckInCheckoutPage(params?: HostelCheckInCheckoutPageQuery) {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  const suffix = qs.size ? `?${qs.toString()}` : "";
  return apiRequest<HostelCheckInCheckoutPage>(
    `/college-admin/hostel-administration/check-ins/management/page${suffix}`,
  );
}