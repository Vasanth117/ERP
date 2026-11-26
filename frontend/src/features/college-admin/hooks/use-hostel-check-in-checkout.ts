"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchHostelCheckInCheckoutPage } from "@/features/college-admin/api/hostel-check-in-checkout";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HostelCheckInCheckoutPageQuery } from "@/features/college-admin/types/hostel-check-in-checkout";

export function useHostelCheckInCheckoutPage(params?: HostelCheckInCheckoutPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hostelCheckInCheckoutPage(params),
    queryFn: () => fetchHostelCheckInCheckoutPage(params),
  });
}