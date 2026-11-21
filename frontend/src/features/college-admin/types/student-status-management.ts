export type StudentStatusManagementTableRow = {
  request_id: string;
  student_name: string;
  register_number: string;
  current_status_label: string;
  new_status_label: string;
  reason_label: string;
  approval_status_label: string;
  approval_status_tone: string;
};

export type StudentStatusManagementMixItem = {
  status_key: string;
  status_label: string;
  count: number;
  bar_percent: number;
  tone: string;
};

export type StudentStatusManagementPage = {
  page_title: string;
  page_subtitle: string;
  change_status_label: string;
  change_status_href: string;
  status_changes_section_title: string;
  table_headers: string[];
  status_change_rows: StudentStatusManagementTableRow[];
  showing_label: string;
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    page_numbers: number[];
    has_previous: boolean;
    has_next: boolean;
  };
  status_mix_title: string;
  status_mix_items: StudentStatusManagementMixItem[];
  update_status_section_title: string;
  student_field_label: string;
  new_status_field_label: string;
  reason_field_label: string;
  submit_status_label: string;
  approve_status_label: string;
  student_picker_options: { record_id: string; label: string }[];
  new_status_options: { value: string; label: string }[];
  selected_request_id: string | null;
  form_record_id: string;
  form_new_status: string;
  form_reason: string;
  updated_at_label: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type StudentStatusManagementPageQuery = {
  page?: number;
  selected_request_id?: string;
};

export type StudentStatusChangeSubmitPayload = {
  record_id: string;
  new_status_bucket: string;
  reason: string;
  approve_immediately?: boolean;
  page?: number;
};

export type StudentStatusApprovePayload = {
  request_id: string;
  page?: number;
};