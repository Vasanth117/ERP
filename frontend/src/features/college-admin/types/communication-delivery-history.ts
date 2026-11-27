import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type CommunicationDeliveryPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type CommunicationDeliveryRow = {
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

export type CommunicationDeliveryStatusPage = {
  page_title: string;
  page_subtitle: string;
  retry_action_label: string;
  retry_enabled: boolean;
  kpis: UserDashboardKpi[];
  deliveries_section_title: string;
  table_headers: string[];
  delivery_rows: CommunicationDeliveryRow[];
  empty_table_message: string;
  showing_label: string;
  count_footer_label: string;
  pagination: CommunicationDeliveryPagination;
  generated_at: string;
};

export type CommunicationHistoryRow = {
  announcement_id: string;
  title: string;
  audience_label: string;
  channels_label: string;
  published_label: string;
  reach_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type CommunicationHistoryFilterOption = { value: string; label: string };

export type CommunicationHistoryPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  export_api_path: string;
  search_placeholder: string;
  month_filter_label: string;
  channel_filter_label: string;
  sender_filter_label: string;
  month_options: CommunicationHistoryFilterOption[];
  channel_options: CommunicationHistoryFilterOption[];
  sender_options: CommunicationHistoryFilterOption[];
  announcements_section_title: string;
  table_headers: string[];
  announcement_rows: CommunicationHistoryRow[];
  empty_table_message: string;
  showing_label: string;
  count_footer_label: string;
  pagination: CommunicationDeliveryPagination;
  generated_at: string;
};