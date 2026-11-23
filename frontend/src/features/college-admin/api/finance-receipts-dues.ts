import { apiRequest } from "@/lib/api/client";

import type { OutstandingDuesManagementPage, OutstandingDuesManagementPageQuery } from "@/features/college-admin/types/outstanding-dues-page";
import type { ReceiptManagementPage, ReceiptManagementPageQuery } from "@/features/college-admin/types/receipt-management";

function toSearch(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchReceiptManagementPage(params?: ReceiptManagementPageQuery) {
  return apiRequest<ReceiptManagementPage>(
    `/college-admin/finance-administration/receipts/page${toSearch(params ?? {})}`,
  );
}

export function fetchOutstandingDuesManagementPage(params?: OutstandingDuesManagementPageQuery) {
  return apiRequest<OutstandingDuesManagementPage>(
    `/college-admin/finance-administration/dues/outstanding/page${toSearch(params ?? {})}`,
  );
}