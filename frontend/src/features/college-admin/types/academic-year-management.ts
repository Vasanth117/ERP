export type AcademicYearManagementTableRow = {
  year_id: string;
  label: string;
  start_label: string;
  end_label: string;
  student_count: number;
  status_code: string;
  status_label: string;
  status_tone: string;
};

export type AcademicYearClosingChecklistItem = {
  key: string;
  title: string;
  detail: string | null;
  completed: boolean;
};

export type AcademicYearRuleToggle = {
  key: string;
  title: string;
  description: string;
  enabled: boolean;
};

export type AcademicYearCreateFormField = {
  key: string;
  label: string;
  required: boolean;
  field_type: string;
};

export type AcademicYearCreateFormOption = {
  value: string;
  label: string;
};

export type YearsSemestersSubNavItem = {
  key: string;
  label: string;
  href: string;
  active: boolean;
};

export type AcademicYearManagementPage = {
  page_title: string;
  page_subtitle: string;
  close_current_year_label: string;
  close_current_year_enabled: boolean;
  close_target_year_label: string | null;
  new_academic_year_label: string;
  academic_years_table_title: string;
  table_headers: string[];
  academic_years: AcademicYearManagementTableRow[];
  academic_year_count_label: string;
  page: number;
  page_size: number;
  total_pages: number;
  total_years: number;
  create_section_title: string;
  create_form_note: string;
  create_submit_label: string;
  cancel_label: string;
  create_fields: AcademicYearCreateFormField[];
  copy_from_options: AcademicYearCreateFormOption[];
  semester_count_options: AcademicYearCreateFormOption[];
  checklist_title: string;
  checklist_items: AcademicYearClosingChecklistItem[];
  rules_section_title: string;
  rules: AcademicYearRuleToggle[];
  sub_nav: YearsSemestersSubNavItem[];
  semesters_button_label: string;
  semesters_button_href: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type AcademicYearManagementCreatePayload = {
  label: string;
  copy_from_year_id?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  semester_count: number;
  admission_intake_opens?: string | null;
};

export type AcademicYearManagementRulesPayload = {
  only_one_current_year: boolean;
  lock_closed_years: boolean;
};