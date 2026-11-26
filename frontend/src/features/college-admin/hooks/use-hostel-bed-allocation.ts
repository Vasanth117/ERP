"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchHostelBedAllocationPage } from "@/features/college-admin/api/hostel-bed-allocation";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HostelBedAllocationPageQuery } from "@/features/college-admin/types/hostel-bed-allocation";

export function useHostelBedAllocationPage(params?: HostelBedAllocationPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hostelBedAllocationPage(params),
    queryFn: () => fetchHostelBedAllocationPage(params),
  });
}