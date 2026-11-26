"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchHostelMessManagementPage } from "@/features/college-admin/api/hostel-mess-management";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useHostelMessManagementPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hostelMessManagementPage(),
    queryFn: () => fetchHostelMessManagementPage(),
  });
}