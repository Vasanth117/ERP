import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type CommunicationAudiencePagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type CommunicationAudienceDeliveryRow = {
  row_key: string;
  message_label: string;
  channel_label: string;
  recipients_count: number;
  delivered_count: number;
  failed_count: number;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type CommunicationFacultyNotificationRow = {
  row_key: string;
  notification_label: string;
  audience_label: string;
  sent_label: string;
  read_label: string;
  acknowledged_label: string;
  detail_href: string;
};

export type CommunicationParentMessageRow = {
  row_key: string;
  message_label: string;
  audience_label: string;
  channel_label: string;
  sent_label: string;
  delivered_label: string;
  detail_href: string;
};

export type CommunicationStudentNotificationsPage = {
  page_title: string;
  page_subtitle: string;
  new_notification_label: string;
  new_notification_href: string;
  kpis: UserDashboardKpi[];
  deliveries_section_title: string;
  table_headers: string[];
  delivery_rows: CommunicationAudienceDeliveryRow[];
  empty_table_message: string;
  showing_label: string;
  count_footer_label: string;
  pagination: CommunicationAudiencePagination;
  generated_at: string;
};

export type CommunicationFacultyNotificationsPage = {
  page_title: string;
  page_subtitle: string;
  new_notification_label: string;
  new_notification_href: string;
  kpis: UserDashboardKpi[];
  recent_section_title: string;
  table_headers: string[];
  notification_rows: CommunicationFacultyNotificationRow[];
  empty_table_message: string;
  showing_label: string;
  count_footer_label: string;
  pagination: CommunicationAudiencePagination;
  generated_at: string;
};

export type CommunicationParentCommunicationPage = {
  page_title: string;
  page_subtitle: string;
  new_message_label: string;
  new_message_href: string;
  kpis: UserDashboardKpi[];
  recent_section_title: string;
  table_headers: string[];
  message_rows: CommunicationParentMessageRow[];
  empty_table_message: string;
  showing_label: string;
  count_footer_label: string;
  pagination: CommunicationAudiencePagination;
  generated_at: string;
};