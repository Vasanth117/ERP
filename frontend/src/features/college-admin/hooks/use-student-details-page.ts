"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchStudentDetailsPage } from "@/features/college-admin/api/students";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useStudentDetailsPage(recordId: string | null) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentDetailsPage(recordId ?? ""),
    queryFn: () => fetchStudentDetailsPage(recordId!),
    enabled: Boolean(recordId),
  });
}