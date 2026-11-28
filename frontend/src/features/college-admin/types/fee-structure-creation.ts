export type FeeStructureCreationProgrammeOption = {
  programme_code: string;
  programme_label: string;
  department_id?: string | null;
  department_name?: string | null;
  programme_level?: string | null;
  stream_label?: string | null;
};

export type FeeStructureCreationPage = {
  page_title: string;
  page_subtitle: string;
  department_filter_label: string;
  stream_filter_label: string;
  programme_filter_label: string;
  academic_year_filter_label: string;
  semester_filter_label: string;
  department_options: { value: string; label: string }[];
  stream_options: { value: string; label: string }[];
  programme_options: FeeStructureCreationProgrammeOption[];
  academic_year_options: { value: string; label: string }[];
  semester_options: { value: string; label: string }[];
  default_line_items: { name: string; amount: number }[];
  save_draft_label: string;
  continue_label: string;
  publish_label: string;
  generated_at: string;
};

export type FeeStructureUpsertPayload = {
  structure_id: string;
  programme_code: string;
  academic_year_label: string;
  semester_label: string;
  line_items: Record<string, unknown>[];
  total_amount: number;
};