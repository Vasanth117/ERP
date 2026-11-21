export type StudentTransferManagementTableRow = {
  request_key: string;
  request_number: string;
  student_name: string;
  from_label: string;
  to_label: string;
  type_label: string;
  status_label: string;
  status_tone: string;
};

export type StudentTransferApprovalStep = {
  key: string;
  label: string;
  status_label: string;
  tone: string;
};

export type StudentTransferManagementPage = {
  page_title: string;
  page_subtitle: string;
  new_transfer_label: string;
  new_transfer_href: string;
  requests_section_title: string;
  table_headers: string[];
  transfer_rows: StudentTransferManagementTableRow[];
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
  selected_request_key: string | null;
  review_section_title: string;
  review_student_field_label: string;
  review_student_line: string;
  review_transfer_type_field_label: string;
  review_transfer_type_options: { value: string; label: string }[];
  review_transfer_type: string;
  review_effective_field_label: string;
  review_effective_options: { value: string; label: string }[];
  review_effective_semester: string;
  review_reason_field_label: string;
  review_reason: string;
  save_review_label: string;
  approve_college_label: string;
  approval_route_title: string;
  approval_steps: StudentTransferApprovalStep[];
  updated_at_label: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type StudentTransferManagementPageQuery = {
  page?: number;
  selected_request_key?: string;
};

export type StudentTransferReviewPayload = {
  request_key: string;
  transfer_type?: string;
  effective_semester?: string;
  reason?: string;
  approve_college?: boolean;
  page?: number;
};