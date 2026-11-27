export type CommunicationAnnouncementsTableRow = {
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

export type CommunicationFilterOption = {
  value: string;
  label: string;
};

export type CommunicationAnnouncementsPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type CommunicationAnnouncementsManagementPage = {
  page_title: string;
  page_subtitle: string;
  new_announcement_label: string;
  new_announcement_href: string;
  search_placeholder: string;
  audience_filter_label: string;
  status_filter_label: string;
  audience_options: CommunicationFilterOption[];
  status_options: CommunicationFilterOption[];
  announcements_section_title: string;
  table_headers: string[];
  announcement_rows: CommunicationAnnouncementsTableRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: CommunicationAnnouncementsPagination;
  generated_at: string;
};

export type CommunicationAnnouncementsPageQuery = {
  page?: number;
  page_size?: number;
  search?: string;
  audience?: string;
  status?: string;
};