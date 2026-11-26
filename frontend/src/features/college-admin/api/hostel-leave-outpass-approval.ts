import { apiRequest } from "@/lib/api/client";

import type {
  HostelLeaveOutpassApprovalPage,
  HostelLeaveOutpassApprovalPageQuery,
} from "@/features/college-admin/types/hostel-leave-outpass-approval";

export function fetchHostelLeaveOutpassApprovalPage(params?: HostelLeaveOutpassApprovalPageQuery) {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  const suffix = qs.size ? `?${qs.toString()}` : "";
  return apiRequest<HostelLeaveOutpassApprovalPage>(
    `/college-admin/hostel-administration/outpass/management/page${suffix}`,
  );
}