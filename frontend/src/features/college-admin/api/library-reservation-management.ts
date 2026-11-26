import { apiRequest } from "@/lib/api/client";

import type {
  LibraryReservationManagementPage,
  LibraryReservationManagementPageQuery,
} from "@/features/college-admin/types/library-reservation-management";

function buildQuery(params?: LibraryReservationManagementPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchLibraryReservationManagementPage(params?: LibraryReservationManagementPageQuery) {
  return apiRequest<LibraryReservationManagementPage>(
    `/college-admin/library-administration/reservations/management/page${buildQuery(params)}`,
  );
}