"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchAcademicConfigurationDashboardPage } from "@/features/college-admin/api/academics";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useAcademicConfigurationDashboardPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.academicConfigurationDashboard(),
    queryFn: fetchAcademicConfigurationDashboardPage,
  });
}