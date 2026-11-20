"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchCreateNewUserPage,
  saveCreateNewUserDraft,
  submitCreateNewUser,
  validateCreateNewUser,
} from "@/features/college-admin/api/users";
import {
  collegeAdminQueryKeys,
  createNewUserPageQueryKey,
} from "@/features/college-admin/query-keys";

export function useCreateNewUserPage() {
  return useQuery({
    queryKey: createNewUserPageQueryKey,
    queryFn: fetchCreateNewUserPage,
  });
}

export function useSaveCreateNewUserDraft() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: saveCreateNewUserDraft,
    onSuccess: (data) => {
      qc.setQueryData(createNewUserPageQueryKey, data);
    },
  });
}

export function useValidateCreateNewUser() {
  return useMutation({
    mutationFn: validateCreateNewUser,
  });
}

export function useSubmitCreateNewUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: submitCreateNewUser,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}