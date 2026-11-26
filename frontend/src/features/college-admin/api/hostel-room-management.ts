import { apiRequest } from "@/lib/api/client";

import type { HostelRoomManagementPage, HostelRoomManagementPageQuery } from "@/features/college-admin/types/hostel-room-management";

export function fetchHostelRoomManagementPage(params?: HostelRoomManagementPageQuery) {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  if (params?.search) qs.set("search", params.search);
  if (params?.block_code) qs.set("block_code", params.block_code);
  if (params?.floor_id) qs.set("floor_id", params.floor_id);
  if (params?.room_type) qs.set("room_type", params.room_type);
  const suffix = qs.size ? `?${qs.toString()}` : "";
  return apiRequest<HostelRoomManagementPage>(`/college-admin/hostel-administration/rooms/management/page${suffix}`);
}