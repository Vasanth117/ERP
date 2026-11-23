"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation } from "@tanstack/react-query";

import {
  createStudentTransferRequest,
  fetchStudentTransferCreatePage,
} from "@/features/college-admin/api/students";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { StudentTransferCreatePayload } from "@/features/college-admin/types/student-transfer-create";

export function useStudentTransferCreatePage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentTransferCreatePage(),
    queryFn: () => fetchStudentTransferCreatePage(),
  });
}

export function useCreateStudentTransferRequest() {
  return useMutation({
    mutationFn: (payload: StudentTransferCreatePayload) => createStudentTransferRequest(payload),
  });
}