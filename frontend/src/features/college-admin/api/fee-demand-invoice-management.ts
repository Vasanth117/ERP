import { apiRequest } from "@/lib/api/client";

import type {
  FeeDemandInvoiceManagementPage,
  FeeDemandInvoiceManagementPageQuery,
} from "@/features/college-admin/types/fee-demand-invoice-management";

export function fetchFeeDemandInvoiceManagementPage(params?: FeeDemandInvoiceManagementPageQuery) {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  const qs = search.toString();
  return apiRequest<FeeDemandInvoiceManagementPage>(
    `/college-admin/finance-administration/invoices/page${qs ? `?${qs}` : ""}`,
  );
}