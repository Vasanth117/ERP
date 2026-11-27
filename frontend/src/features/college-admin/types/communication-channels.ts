import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type CommunicationChannelPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type CommunicationChannelAlertBanner = {
  tone: string;
  message: string;
  link_label: string;
  link_href: string;
};

export type CommunicationEmailCampaignRow = {
  row_key: string;
  campaign_label: string;
  audience_label: string;
  sent_label: string;
  opened_label: string;
  bounced_count: number;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type CommunicationEmailChannelPage = {
  page_title: string;
  page_subtitle: string;
  primary_action_label: string;
  primary_action_href: string;
  kpis: UserDashboardKpi[];
  campaigns_section_title: string;
  table_headers: string[];
  campaign_rows: CommunicationEmailCampaignRow[];
  empty_table_message: string;
  count_footer_label: string;
  showing_label: string;
  pagination: CommunicationChannelPagination;
  generated_at: string;
};

export type CommunicationSmsBatchRow = {
  row_key: string;
  batch_label: string;
  template_label: string;
  recipients_count: number;
  delivered_count: number;
  failed_count: number;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type CommunicationSmsChannelPage = {
  page_title: string;
  page_subtitle: string;
  primary_action_label: string;
  primary_action_href: string;
  kpis: UserDashboardKpi[];
  batches_section_title: string;
  table_headers: string[];
  batch_rows: CommunicationSmsBatchRow[];
  empty_table_message: string;
  count_footer_label: string;
  showing_label: string;
  pagination: CommunicationChannelPagination;
  generated_at: string;
};

export type CommunicationWhatsappTemplateRow = {
  row_key: string;
  template_label: string;
  category_label: string;
  language_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type CommunicationWhatsappChannelPage = {
  page_title: string;
  page_subtitle: string;
  primary_action_label: string;
  primary_action_href: string;
  primary_action_style: string;
  alert_banner: CommunicationChannelAlertBanner | null;
  kpis: UserDashboardKpi[];
  templates_section_title: string;
  table_headers: string[];
  template_rows: CommunicationWhatsappTemplateRow[];
  empty_table_message: string;
  count_footer_label: string;
  showing_label: string;
  pagination: CommunicationChannelPagination;
  generated_at: string;
};