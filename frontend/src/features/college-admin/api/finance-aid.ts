import { apiRequest } from "@/lib/api/client";

import type {
  ConcessionWaiverManagementPage,
  ConcessionWaiverManagementPageQuery,
} from "@/features/college-admin/types/fee-concession-waiver-management";
import type { RefundManagementPage, RefundManagementPageQuery } from "@/features/college-admin/types/refund-management-page";
import type { ScholarshipManagementPage, ScholarshipManagementPageQuery } from "@/features/college-admin/types/scholarship-management";

function toSearch(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchScholarshipManagementPage(params?: ScholarshipManagementPageQuery) {
  return apiRequest<ScholarshipManagementPage>(
    `/college-admin/finance-administration/aid/scholarships/page${toSearch(params ?? {})}`,
  );
}

export function fetchConcessionWaiverManagementPage(params?: ConcessionWaiverManagementPageQuery) {
  return apiRequest<ConcessionWaiverManagementPage>(
    `/college-admin/finance-administration/aid/concessions/page${toSearch(params ?? {})}`,
  );
}

export function fetchRefundManagementPage(params?: RefundManagementPageQuery) {
  return apiRequest<RefundManagementPage>(
    `/college-admin/finance-administration/aid/refunds/page${toSearch(params ?? {})}`,
  );
}