export type BulkUserInvitationWizardStep = {
  key: string;
  label: string;
  step_number: number;
};

export type BulkUserInvitationToggle = {
  key: string;
  label: string;
  description: string;
  default_on: boolean;
};

export type BulkUserInvitationSummaryStat = {
  key: string;
  label: string;
  count: number;
  description: string;
  tone: string;
};

export type BulkUserInvitationPreviewRow = {
  row_id: string;
  full_name: string;
  email: string;
  role_label: string;
  department_label: string;
  status_code: string;
  status_label: string;
  status_tone: string;
};

export type BulkUserInvitationPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
  showing_label: string;
};

export type BulkUserInvitationPage = {
  page_title: string;
  page_subtitle: string;
  download_template_label: string;
  send_invitations_label: string;
  cancel_href: string;
  cancel_label: string;
  audit_footer_note: string;
  back_label: string;
  fix_errors_label: string;
  send_ready_label: string;
  browse_files_label: string;
  upload_drop_hint: string;
  preview_section_title: string;
  preview_summary_label: string | null;
  validation_summary_title: string;
  invitation_options_title: string;
  table_headers: string[];
  current_step_key: string;
  steps: BulkUserInvitationWizardStep[];
  file_name: string | null;
  file_meta_label: string | null;
  summary_stats: BulkUserInvitationSummaryStat[];
  invitation_toggles: BulkUserInvitationToggle[];
  preview_rows: BulkUserInvitationPreviewRow[];
  pagination: BulkUserInvitationPagination;
  ready_to_send_count: number;
  footer_disclaimer: string;
  generated_at: string;
};

export type BulkUserInvitationSendResult = {
  status: string;
  message: string;
  sent_count: number;
  skipped_count: number;
  href: string;
};