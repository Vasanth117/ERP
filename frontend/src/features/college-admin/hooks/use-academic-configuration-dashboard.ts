"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchAcademicConfigurationDashboardPage } from "@/features/college-admin/api/academics";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useAcademicConfigurationDashboardPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.academicConfigurationDashboard(),
    queryFn: fetchAcademicConfigurationDashboardPage,
  });
}