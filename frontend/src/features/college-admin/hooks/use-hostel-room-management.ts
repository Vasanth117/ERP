"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchHostelRoomManagementPage } from "@/features/college-admin/api/hostel-room-management";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HostelRoomManagementPageQuery } from "@/features/college-admin/types/hostel-room-management";

export function useHostelRoomManagementPage(params?: HostelRoomManagementPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hostelRoomManagementPage(params),
    queryFn: () => fetchHostelRoomManagementPage(params),
  });
}