import type {
  AcademicYearCreateFormOption,
  YearsSemestersSubNavItem,
} from "@/features/college-admin/types/academic-year-management";

export type SemesterManagementTableRow = {
  term_id: string;
  label: string;
  period_label: string;
  week_label: string;
  course_count: number;
  status_code: string;
  status_label: string;
  status_tone: string;
  is_current: boolean;
};

export type SemesterSettingsForm = {
  teaching_starts: string | null;
  last_instruction_day: string | null;
  mid_semester_exam_date: string | null;
  end_semester_exam_date: string | null;
  course_registration_opens: string | null;
  add_drop_deadline: string | null;
};

export type SemesterManagementPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  new_semester_label: string;
  year_filter_options: AcademicYearCreateFormOption[];
  selected_academic_year_id: string | null;
  selected_academic_year_label: string;
  semesters_panel_title: string;
  table_headers: string[];
  semester_rows: SemesterManagementTableRow[];
  semester_count_label: string;
  manage_terms_href: string;
  manage_terms_label: string;
  selected_term_id: string | null;
  settings_panel_title: string;
  settings_form: SemesterSettingsForm | null;
  settings_field_meta: { key: string; label: string; required: boolean }[];
  save_label: string;
  cancel_label: string;
  settings_form_note: string;
  progress_section_title: string;
  progress_items: { key: string; label: string; progress_percent: number }[];
  linked_section_title: string;
  linked_items: {
    key: string;
    title: string;
    subtitle: string;
    status_label: string;
    status_tone: string;
  }[];
  sub_nav: YearsSemestersSubNavItem[];
  years_button_label: string;
  years_button_href: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type SemesterSettingsSavePayload = {
  term_id: string;
  settings: {
    teaching_starts: string | null;
    last_instruction_day: string | null;
    mid_semester_exam_date: string | null;
    end_semester_exam_date: string | null;
    course_registration_opens: string | null;
    add_drop_deadline: string | null;
  };
};

export type SemesterCreatePayload = {
  academic_year_id: string;
  label: string;
  term_code?: string | null;
};