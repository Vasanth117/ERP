"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchDepartmentWiseAttendancePage } from "@/features/college-admin/api/department-wise-attendance";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { DepartmentWiseAttendanceQuery } from "@/features/college-admin/types/department-wise-attendance";

export function useDepartmentWiseAttendancePage(params?: DepartmentWiseAttendanceQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.departmentWiseAttendance(params),
    queryFn: () => fetchDepartmentWiseAttendancePage(params),
  });
}