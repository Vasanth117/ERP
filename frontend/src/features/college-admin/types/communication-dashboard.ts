import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type CommunicationDashboardDeliveryRow = {
  batch_key: string;
  message_label: string;
  channel_label: string;
  recipients_count: number;
  delivered_count: number;
  failed_count: number;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type CommunicationChannelSidebarItem = {
  channel_key: string;
  title: string;
  subtitle_line: string;
  status_label: string;
  status_tone: string;
  icon_key: string;
  href: string;
};

export type CommunicationDashboardPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type CommunicationDashboardPage = {
  page_title: string;
  page_subtitle: string;
  create_announcement_label: string;
  create_announcement_href: string;
  kpis: UserDashboardKpi[];
  deliveries_section_title: string;
  table_headers: string[];
  delivery_rows: CommunicationDashboardDeliveryRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: CommunicationDashboardPagination;
  channels_section_title: string;
  channel_items: CommunicationChannelSidebarItem[];
  generated_at: string;
};

export type CommunicationDashboardPageQuery = {
  page?: number;
  page_size?: number;
};