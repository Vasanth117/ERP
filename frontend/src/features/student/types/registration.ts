export type AvailableCourse = {
  course_id: string;
  course_code: string;
  name: string;
  credit_units: number;
  registration_type: string;
  is_open_for_registration: boolean;
  prerequisites_met: boolean | null;
  max_capacity: number | null;
};

export type ElectiveGroup = {
  id: string;
  group_code: string;
  title: string;
  description: string | null;
  min_selections: number;
  max_selections: number;
  min_credits: number;
  max_credits: number;
};

export type ElectiveOption = {
  course_id: string;
  course_code: string;
  course_name: string;
  credit_units: number;
  seats_available: number | null;
  eligible: boolean;
};

export type RegistrationEligibility = {
  eligible: boolean;
  reasons: string[];
  min_credits: number | null;
  max_credits: number | null;
  registration_open_at: string | null;
  registration_close_at: string | null;
  modification_deadline: string | null;
  window_open: boolean;
};

export type RegistrationSelectionInput = {
  course_id: string;
  course_code: string;
  section_code?: string | null;
  registration_type?: string;
  elective_group_id?: string | null;
};

export type RegistrationValidation = {
  valid: boolean;
  errors: string[];
  warnings: string[];
  total_credits: number;
  timetable_conflicts: string[];
};

export type RegistrationSubmit = {
  request_id: string;
  status: string;
  selections: RegistrationSelectionInput[];
  submitted_at: string | null;
};

export type CourseRegistration = {
  id: string;
  course_id: string;
  course_code: string;
  section_code: string | null;
  registration_type: string;
  credit_units: number;
  status: string;
  academic_year_label: string;
  semester_label: string;
};

export type RegistrationRequest = {
  id: string;
  status: string;
  academic_year_label: string;
  semester_label: string;
  selections: RegistrationSelectionInput[];
  reviewer_note: string | null;
  submitted_at: string | null;
  resolved_at: string | null;
};

export type RegistrationHistory = {
  id: string;
  course_code: string;
  action: string;
  previous_status: string | null;
  new_status: string | null;
  occurred_at: string;
};

export type RegistrationOverviewStep = {
  key: string;
  label: string;
  state: "completed" | "current" | "upcoming";
};

export type RegistrationOverviewKpis = {
  window_label: string;
  window_hint: string | null;
  credit_limit_label: string;
  selected_count: string;
  status_label: string;
};

export type RegistrationOverviewCourseRow = {
  course_code: string;
  course_name: string;
  category_label: string;
  credit_units: number;
  prerequisite_label: string;
  seats_label: string;
};

export type RegistrationPrerequisiteCheck = {
  key: string;
  title: string;
  detail: string;
  status_label: string;
  status_tone: string;
};

export type RegistrationClosedPanel = {
  page_title: string;
  page_subtitle: string;
  banner_title: string;
  banner_body: string;
  raise_request_href: string;
  window_opened_label: string;
  window_closed_label: string;
  student_status_label: string;
  show_late_registration_banner: boolean;
  show_raise_request_action: boolean;
};

export type RegistrationFilterOption = {
  value: string;
  label: string;
};

export type RegistrationCourseListRow = {
  course_id: string;
  course_code: string;
  course_name: string;
  category_label: string;
  credit_units: number;
  prerequisite_label: string;
  seats_label: string;
  is_selectable: boolean;
};

export type RegistrationCoursesPage = {
  page_title: string;
  page_subtitle: string;
  go_to_selection_href: string;
  semester_options: RegistrationFilterOption[];
  category_options: RegistrationFilterOption[];
  selected_semester: string;
  selected_category: string;
  search_placeholder: string;
  courses: RegistrationCourseListRow[];
  courses_footer_label: string;
  default_course_code: string | null;
};

export type RegistrationCourseDetailPage = {
  page_title: string;
  headline: string;
  course_code: string;
  course_name: string;
  category_label: string;
  credit_units: number;
  faculty_label: string;
  seats_label: string;
  slot_label: string;
  description: string;
  eligibility: RegistrationPrerequisiteCheck[];
  add_to_selection_href: string;
  show_add_to_selection: boolean;
  back_href: string;
};

export type RegistrationElectiveOptionChoice = {
  course_id: string;
  course_code: string;
  course_name: string;
  choice_label: string;
  credit_units: number;
  eligible: boolean;
};

export type RegistrationElectiveGroupSelection = {
  group_id: string;
  title: string;
  choose_label: string;
  selected_course_id: string | null;
  alternate_course_id: string | null;
  primary_options: RegistrationElectiveOptionChoice[];
  alternate_options: RegistrationElectiveOptionChoice[];
};

export type RegistrationElectiveCreditCheck = {
  selected_detail: string;
  allowed_range: string;
  status_label: string;
  status_tone: string;
  min_credits: number | null;
  max_credits: number | null;
};

export type RegistrationElectiveSelectionSection = {
  page_title: string;
  page_subtitle: string;
  steps: RegistrationOverviewStep[];
  active_step_index: number;
  cancel_href: string;
  review_href: string;
  draft_request_id: string | null;
  groups: RegistrationElectiveGroupSelection[];
  credit_check: RegistrationElectiveCreditCheck;
};

export type RegistrationElectiveCatalogueRow = {
  course_code: string;
  course_name: string;
  seats_label: string;
};

export type RegistrationElectiveCatalogueGroup = {
  title: string;
  courses: RegistrationElectiveCatalogueRow[];
  footer_label: string;
};

export type RegistrationElectiveCatalogueSection = {
  page_title: string;
  page_subtitle: string;
  groups: RegistrationElectiveCatalogueGroup[];
};

export type RegistrationElectivesPage = {
  selection: RegistrationElectiveSelectionSection;
  catalogue: RegistrationElectiveCatalogueSection;
};

export type RegistrationReviewSelectedRow = {
  course_id: string;
  course_code: string;
  course_name: string;
  category_label: string;
  credit_units: number;
  registration_type: string;
  elective_group_id: string | null;
};

export type RegistrationReviewTotals = {
  course_count: number;
  credit_units: number;
  fees_label: string;
};

export type RegistrationReviewSummarySection = {
  page_title: string;
  page_subtitle: string;
  steps: RegistrationOverviewStep[];
  active_step_index: number;
  back_href: string;
  submit_enabled: boolean;
  selected_rows: RegistrationReviewSelectedRow[];
  footer_label: string;
  totals: RegistrationReviewTotals;
  declaration_label: string;
  draft_request_id: string | null;
};

export type RegistrationReviewValidationCheck = {
  check_key: string;
  check_label: string;
  course_label: string;
  result_label: string;
  result_tone: string;
};

export type RegistrationReviewValidationSection = {
  page_title: string;
  page_subtitle: string;
  steps: RegistrationOverviewStep[];
  active_step_index: number;
  fix_selection_href: string;
  alert_title: string | null;
  alert_body: string | null;
  checks: RegistrationReviewValidationCheck[];
  checks_footer_label: string;
  is_valid: boolean;
};

export type RegistrationReviewConfirmationDetail = {
  key: string;
  label: string;
  value: string;
};

export type RegistrationReviewConfirmationSection = {
  page_title: string;
  page_subtitle: string;
  steps: RegistrationOverviewStep[];
  active_step_index: number;
  is_submitted: boolean;
  success_title: string;
  success_body: string;
  pending_title: string | null;
  pending_body: string | null;
  download_slip_href: string | null;
  view_status_href: string;
  details: RegistrationReviewConfirmationDetail[];
};

export type RegistrationReviewPage = {
  summary: RegistrationReviewSummarySection;
  validation: RegistrationReviewValidationSection;
  confirmation: RegistrationReviewConfirmationSection;
  default_sub_panel: "confirmation" | "validation";
};

export type RegistrationStatusCourseRow = {
  course_code: string;
  course_name: string;
  status_label: string;
  status_tone: string;
  credit_units: number;
};

export type RegistrationApprovalStep = {
  key: string;
  label: string;
  detail: string;
  state: string;
  tone: string;
};

export type RegistrationStatusSection = {
  page_title: string;
  page_subtitle: string;
  courses: RegistrationStatusCourseRow[];
  courses_footer_label: string;
  approval_steps: RegistrationApprovalStep[];
};

export type RegistrationHistorySemesterRow = {
  reference_label: string;
  semester_label: string;
  course_count: number;
  credit_units: number;
  submitted_at_label: string;
  status_label: string;
  status_tone: string;
};

export type RegistrationHistorySection = {
  page_title: string;
  page_subtitle: string;
  rows: RegistrationHistorySemesterRow[];
  footer_label: string;
};

export type RegistrationStatusPage = {
  status: RegistrationStatusSection;
  history: RegistrationHistorySection;
};

export type RegistrationOverviewPage = {
  page_title: string;
  page_subtitle: string;
  registration_semester_number: number | null;
  window_open: boolean;
  show_start_registration: boolean;
  start_registration_href: string;
  contact_department_href: string;
  kpis: RegistrationOverviewKpis;
  steps: RegistrationOverviewStep[];
  active_step_index: number;
  available_courses: RegistrationOverviewCourseRow[];
  courses_footer_label: string;
  prerequisite_checks: RegistrationPrerequisiteCheck[];
  closed_panel: RegistrationClosedPanel | null;
};