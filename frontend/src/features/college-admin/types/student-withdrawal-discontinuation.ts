export type StudentWithdrawalWizardStep = {
  key: string;
  label: string;
  step_number: number;
};

export type StudentWithdrawalClearanceRow = {
  department_key: string;
  department_label: string;
  status_label: string;
  status_tone: string;
  cleared_on_label: string;
};

export type StudentWithdrawalProcessStep = {
  key: string;
  label: string;
  status_label: string;
  tone: string;
};

export type StudentWithdrawalDiscontinuationPage = {
  page_title: string;
  page_subtitle: string;
  cancel_label: string;
  cancel_href: string;
  submit_for_approval_label: string;
  wizard_steps: StudentWithdrawalWizardStep[];
  active_step_key: string;
  active_step_index: number;
  withdrawal_request_section_title: string;
  student_field_label: string;
  type_field_label: string;
  last_attendance_field_label: string;
  reason_field_label: string;
  student_line: string;
  selected_record_id: string;
  withdrawal_type: string;
  last_attendance_date: string;
  reason: string;
  withdrawal_type_options: { value: string; label: string }[];
  clearances_section_title: string;
  clearance_table_headers: string[];
  clearance_rows: StudentWithdrawalClearanceRow[];
  clearances_summary_label: string;
  process_section_title: string;
  process_steps: StudentWithdrawalProcessStep[];
  request_id: string | null;
  can_submit: boolean;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type StudentWithdrawalPageQuery = {
  record_id?: string;
  request_id?: string;
};

export type StudentWithdrawalSavePayload = {
  record_id: string;
  request_id?: string | null;
  withdrawal_type?: string | null;
  last_attendance_date?: string | null;
  reason?: string | null;
};

export type StudentWithdrawalSubmitPayload = StudentWithdrawalSavePayload;