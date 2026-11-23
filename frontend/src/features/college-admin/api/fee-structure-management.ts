import { apiRequest } from "@/lib/api/client";

import type {
  FeeStructureManagementPage,
  FeeStructureManagementPageQuery,
} from "@/features/college-admin/types/fee-structure-management";

export function fetchFeeStructureManagementPage(params?: FeeStructureManagementPageQuery) {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  const qs = search.toString();
  return apiRequest<FeeStructureManagementPage>(
    `/college-admin/finance-administration/fee-structures/page${qs ? `?${qs}` : ""}`,
  );
}