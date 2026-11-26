"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchHostelAdmissionApplicationsPage } from "@/features/college-admin/api/hostel-admission-applications";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HostelAdmissionApplicationsPageQuery } from "@/features/college-admin/types/hostel-admission-applications";

export function useHostelAdmissionApplicationsPage(params?: HostelAdmissionApplicationsPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hostelAdmissionApplicationsPage(params),
    queryFn: () => fetchHostelAdmissionApplicationsPage(params),
  });
}