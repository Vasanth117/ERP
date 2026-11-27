export type CommunicationTemplatesPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type CommunicationTemplateManagementRow = {
  row_key: string;
  template_label: string;
  channel_label: string;
  language_label: string;
  variables_count: number;
  updated_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type CommunicationTemplatesManagementPage = {
  page_title: string;
  page_subtitle: string;
  primary_action_label: string;
  primary_action_href: string;
  templates_section_title: string;
  table_headers: string[];
  template_rows: CommunicationTemplateManagementRow[];
  empty_table_message: string;
  count_footer_label: string;
  showing_label: string;
  pagination: CommunicationTemplatesPagination;
  generated_at: string;
};

export type CommunicationScheduledMessageRow = {
  row_key: string;
  message_label: string;
  audience_label: string;
  channels_label: string;
  send_at_label: string;
  created_by_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type CommunicationScheduledMessagesPage = {
  page_title: string;
  page_subtitle: string;
  primary_action_label: string;
  primary_action_href: string;
  scheduled_section_title: string;
  table_headers: string[];
  message_rows: CommunicationScheduledMessageRow[];
  empty_table_message: string;
  count_footer_label: string;
  showing_label: string;
  pagination: CommunicationTemplatesPagination;
  generated_at: string;
};