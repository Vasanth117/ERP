"use client";

import {
  useQuery,
  type QueryKey,
  type UseQueryOptions,
  type UseQueryResult,
} from "@tanstack/react-query";

import { useCollegeAdminDemoQueryKey } from "@/features/college-admin/hooks/use-college-admin-demo-query-key";

type CollegeAdminQueryOptions<TData, TError = Error> = Omit<
  UseQueryOptions<TData, TError, TData, QueryKey>,
  "queryKey" | "queryFn"
> & {
  queryKey: readonly unknown[];
  queryFn: () => Promise<TData>;
};

/** College-admin useQuery with live vs showcase cache separation and demo API header. */
export function useCollegeAdminQuery<TData, TError = Error>(
  options: CollegeAdminQueryOptions<TData, TError>,
): UseQueryResult<TData, TError> {
  const queryKey = useCollegeAdminDemoQueryKey(options.queryKey);
  return useQuery({
    ...options,
    queryKey,
  });
}