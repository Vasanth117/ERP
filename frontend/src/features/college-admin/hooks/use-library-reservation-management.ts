"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchLibraryReservationManagementPage } from "@/features/college-admin/api/library-reservation-management";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { LibraryReservationManagementPageQuery } from "@/features/college-admin/types/library-reservation-management";

export function useLibraryReservationManagementPage(params?: LibraryReservationManagementPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.libraryReservationManagementPage(params),
    queryFn: () => fetchLibraryReservationManagementPage(params),
  });
}