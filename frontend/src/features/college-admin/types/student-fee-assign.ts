export type StudentFeeAssignStructureOption = {
  structure_id: string;
  label: string;
  programme_code: string;
  academic_year_label: string;
  semester_label: string;
  total_amount: number;
  total_label: string;
};

export type StudentFeeAssignStudentOption = {
  student_user_id: string;
  label: string;
  register_number: string;
  programme_code: string | null;
  batch_label: string | null;
  section_code: string | null;
};

export type StudentFeeAssignPage = {
  page_title: string;
  page_subtitle: string;
  single_tab_label: string;
  group_tab_label: string;
  bulk_tab_label: string;
  structure_label: string;
  student_label: string;
  programme_label: string;
  batch_filter_label: string;
  section_filter_label: string;
  concession_label: string;
  assign_submit_label: string;
  bulk_file_label: string;
  bulk_template_hint: string;
  structure_options: StudentFeeAssignStructureOption[];
  student_options: StudentFeeAssignStudentOption[];
  programme_options: { value: string; label: string }[];
  batch_options: { value: string; label: string }[];
  section_options: { value: string; label: string }[];
  generated_at: string;
};

export type FeeAssessmentBulkRow = {
  register_number: string;
  structure_id?: string | null;
  concession_amount?: number;
};

export type FeeAssessmentGroupAssignPayload = {
  structure_id: string;
  programme_code: string;
  batch_label?: string | null;
  section_code?: string | null;
};

export type FeeAssessmentBulkAssignPayload = {
  default_structure_id?: string | null;
  rows: FeeAssessmentBulkRow[];
};

export type FeeAssessmentCreatePayload = {
  student_user_id: string;
  structure_id: string;
  academic_year_label: string;
  semester_label: string;
  concession_amount?: number;
};

export type AssignBatchResult = {
  bulk_batch_id?: string;
  matched?: number;
  processed?: number;
  succeeded: number;
  skipped: number;
  failed: { register_number?: string; student_user_id?: string; message: string }[];
};