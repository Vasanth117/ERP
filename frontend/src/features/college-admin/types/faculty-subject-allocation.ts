export type FacultyAssignmentWorkflowStep = {
  key: string;
  label: string;
  step_number: number;
  status: string;
  href?: string | null;
};

export type FacultySubjectAllocationTableRow = {
  course_id: string;
  subject_name: string;
  subject_code: string;
  semester_label: string;
  hours_label: string;
  faculty_label: string;
  faculty_record_id?: string | null;
  status_label?: string | null;
  status_tone?: string | null;
};

export type FacultySubjectCapacityRow = {
  faculty_record_id: string;
  faculty_name: string;
  hours_assigned_label: string;
  hours_capacity_label: string;
  assigned_hours: number;
  capacity_hours: number;
  load_tone: string;
};

export type StudentAdminDashboardFilterOption = {
  value: string;
  label: string;
};

export type FacultySubjectAllocationPage = {
  page_title: string;
  page_subtitle: string;
  auto_suggest_label: string;
  confirm_label: string;
  semester_filter_label: string;
  department_filter_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  academic_year_options: StudentAdminDashboardFilterOption[];
  department_options: StudentAdminDashboardFilterOption[];
  semester_options: StudentAdminDashboardFilterOption[];
  selected_academic_year: string;
  selected_department_id: string;
  selected_semester_label: string;
  workflow_steps: FacultyAssignmentWorkflowStep[];
  subjects_section_title: string;
  table_headers: string[];
  subject_rows: FacultySubjectAllocationTableRow[];
  subjects_footer_label: string;
  capacity_section_title: string;
  capacity_rows: FacultySubjectCapacityRow[];
  has_pending_suggestions: boolean;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type FacultySubjectAllocationQuery = {
  academic_year_label?: string;
  semester_label?: string;
  department_id?: string;
};