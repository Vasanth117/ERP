export type AttendanceCorrectionKpi = {
  key: string;
  label: string;
  value: string;
  hint_line: string;
  hint_tone: string;
};

export type AttendanceCorrectionRequestRow = {
  row_key: string;
  request_code: string;
  faculty_label: string;
  class_label: string;
  session_date_label: string;
  change_summary: string;
  status_label: string;
  status_tone: string;
  review_href: string;
  review_label: string;
};

export type AttendanceCorrectionRequestsPage = {
  page_title: string;
  page_subtitle: string;
  updated_at_label: string;
  kpis: AttendanceCorrectionKpi[];
  requests_table_title: string;
  requests_table_headers: string[];
  request_rows: AttendanceCorrectionRequestRow[];
  requests_table_footer_label: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type AttendanceCorrectionApprovalStep = {
  key: string;
  label: string;
  status_label: string;
  tone: string;
};

export type FieldOption = {
  value: string;
  label: string;
};

export type AttendanceApprovalPage = {
  page_title: string;
  selected_request_id: string | null;
  request_code: string;
  back_href: string;
  back_label: string;
  reject_label: string;
  approve_label: string;
  request_card_title: string;
  faculty_field_label: string;
  faculty_label: string;
  class_field_label: string;
  class_label: string;
  date_field_label: string;
  session_date_label: string;
  change_field_label: string;
  change_summary: string;
  reason_field_label: string;
  reason_text: string;
  decision_card_title: string;
  decision_field_label: string;
  decision_required: boolean;
  decision_options: FieldOption[];
  selected_decision: string;
  remarks_field_label: string;
  remarks_placeholder: string;
  remarks_value: string;
  approval_route_title: string;
  approval_steps: AttendanceCorrectionApprovalStep[];
  can_decide: boolean;
  decide_blocked_message: string | null;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type AttendanceCorrectionDecidePayload = {
  request_id: string;
  decision: "approved" | "rejected";
  reviewer_note?: string;
};

export type AttendanceCorrectionsListQuery = {
  page?: number;
  page_size?: number;
};