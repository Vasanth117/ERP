"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchCommunicationSectionSubNav } from "@/features/college-admin/api/communication-section-sub-nav";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useCommunicationSectionSubNav(path: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.communicationSectionSubNav(path),
    queryFn: () => fetchCommunicationSectionSubNav(path),
  });
}