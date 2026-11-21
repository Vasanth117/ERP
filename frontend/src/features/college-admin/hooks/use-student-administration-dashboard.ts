"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchStudentAdministrationDashboardPage } from "@/features/college-admin/api/students";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { StudentAdministrationDashboardQuery } from "@/features/college-admin/types/student-administration-dashboard";

export function useStudentAdministrationDashboardPage(params?: StudentAdministrationDashboardQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentAdministrationDashboard(params),
    queryFn: () => fetchStudentAdministrationDashboardPage(params),
  });
}