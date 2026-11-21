"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchFacultyDirectoryPage } from "@/features/college-admin/api/faculty";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { FacultyDirectoryQuery } from "@/features/college-admin/types/faculty-directory";

export function useFacultyDirectoryPage(params?: FacultyDirectoryQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.facultyDirectoryPage(params),
    queryFn: () => fetchFacultyDirectoryPage(params),
  });
}