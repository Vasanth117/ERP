export type AdmissionInfo = {
  student_id: string | null;
  roll_number: string | null;
  admission_number: string | null;
  admission_date: string | null;
  programme_code: string | null;
  programme_name: string | null;
  department_name: string | null;
  batch_label: string | null;
  section_code: string | null;
};

export type EnrollmentStatus = {
  academic_year_label: string;
  semester_label: string;
  enrollment_status: string;
  academic_standing: string;
  progression_status: string;
};

export type DepartmentProgramme = {
  department_id: string | null;
  department_name: string | null;
  programme_code: string | null;
  programme_name: string | null;
  batch_label: string | null;
  section_code: string | null;
};

export type EnrollmentLine = {
  course_code: string;
  course_name: string;
  section_code: string;
  status: string;
  academic_year_label: string;
  semester_label: string;
  category?: string | null;
  credits?: number | null;
  faculty_name?: string | null;
};

export type EnrollmentHistory = {
  id: string;
  academic_year_label: string;
  semester_label: string;
  programme_code: string | null;
  section_code: string | null;
  courses: Record<string, string>[];
  final_standing: string;
  credits_earned: number;
  cgpa: number | null;
  closed_at: string;
};

export type AcademicEligibility = {
  promotion_eligible: boolean | null;
  eligibility_summary: Record<string, unknown>;
  credits_registered: number;
  credits_earned: number;
  cgpa: number | null;
};

export type StudentAcademicInformation = {
  regulation_label: string | null;
  admission_type: string | null;
  batch_display: string | null;
  admission_year: string | null;
  study_mode: string | null;
  current_semester_number: number | null;
  total_semesters: number | null;
  minimum_credits_required: number | null;
  programme_duration_years: number | null;
};

export type StudentAcademicAdvisor = {
  class_advisor_name: string | null;
  mentor_name: string | null;
};

export type ProgrammeDepartmentContext = {
  programme: {
    programme_name: string | null;
    duration_label: string | null;
    total_credits: number | null;
    affiliation_name: string | null;
    accreditation_label: string | null;
  };
  department: {
    department_name: string | null;
    head_of_department_name: string | null;
    class_advisor_name: string | null;
    department_email: string | null;
  };
  contacts: {
    office_location: string | null;
    contact_phone: string | null;
  };
};

export type SemesterAcademicHistoryItem = {
  id: string;
  semester_label: string;
  semester_number: number | null;
  period_label: string | null;
  credits_earned: number;
  credits_required: number | null;
  gpa: number | null;
  result_label: string;
};

export type ProgressionTransition = {
  transition_label: string;
  credits_display: string;
  requirement_label: string;
  outcome: string;
  outcome_tone: string;
};

export type AcademicProgressionDetails = {
  transitions: ProgressionTransition[];
  policy: {
    minimum_attendance_percent: number | null;
    arrears_rule_label: string | null;
    regulation_label: string | null;
  };
};

export type CurrentSemesterOverview = {
  term_subtitle: string | null;
  subject_count: number;
  credits_registered: number;
  internal_tests_label: string | null;
  attendance_percent: number | null;
  next_exam_title: string | null;
  next_exam_date_label: string | null;
};

export type CourseCreditCategoryRow = {
  category: string;
  credits_required: number;
  credits_earned: number;
  credits_in_progress: number;
  credits_remaining: number;
};

export type CourseCreditSummary = {
  credits_earned: number;
  credits_in_progress: number;
  credits_remaining: number;
  credits_required: number;
  in_progress_semester_label: string | null;
  categories: CourseCreditCategoryRow[];
};

export type SemesterSubjectsTerm = {
  academic_year_label: string;
  semester_label: string;
  semester_number: number | null;
  is_current: boolean;
  subjects: EnrollmentLine[];
};

export type EnrollmentConfirmation = {
  page_subtitle: string | null;
  window_banner_title: string | null;
  window_banner_body: string | null;
  target_semester_number: number | null;
  target_academic_year_label: string | null;
  target_semester_label: string | null;
  eligibility_label: string | null;
  fee_clearance_label: string | null;
  attendance_condition_label: string | null;
  declaration_accepted: boolean;
  window_open: boolean;
  can_confirm: boolean;
  already_confirmed: boolean;
  confirmed_at: string | null;
  confirm_blocked_reasons?: string[];
};

export type EnrollmentConfirmationHistoryRow = {
  id: string;
  academic_year_label: string;
  semester_label: string;
  semester_number: number | null;
  study_mode: string | null;
  confirmed_on_label: string | null;
  status: string;
  status_tone: string;
};

export type AcademicStatusStandingField = {
  label: string;
  value: string;
};

export type AcademicStatusPendingRequirement = {
  title: string;
  detail: string | null;
  status_label: string;
  status_tone: string;
  icon_tone: string;
  action_href?: string | null;
};

export type AcademicStatusDetails = {
  page_subtitle: string | null;
  standing_fields: AcademicStatusStandingField[];
  pending_requirements: AcademicStatusPendingRequirement[];
};

export type AcademicDetails = {
  admission: AdmissionInfo;
  enrollment_status: EnrollmentStatus;
  department_programme: DepartmentProgramme;
  current_enrollments: EnrollmentLine[];
  academic_record: AcademicEligibility | null;
  academic_information: StudentAcademicInformation;
  advisors: StudentAcademicAdvisor;
  programme_department_context?: ProgrammeDepartmentContext | null;
  current_semester_overview?: CurrentSemesterOverview | null;
  semester_academic_history?: SemesterAcademicHistoryItem[];
  academic_progression?: AcademicProgressionDetails | null;
  course_credit_summary?: CourseCreditSummary | null;
  semester_subject_terms?: SemesterSubjectsTerm[];
  enrollment_confirmation?: EnrollmentConfirmation | null;
  enrollment_confirmation_history?: EnrollmentConfirmationHistoryRow[];
  academic_status_details?: AcademicStatusDetails | null;
};

export type EnrollmentRequestCreate = {
  request_type: string;
  title: string;
  description: string;
  payload?: Record<string, unknown>;
};

export type EnrollmentRequest = {
  id: string;
  request_type: string;
  title: string;
  description: string;
  status: string;
  academic_year_label: string;
  semester_label: string;
  reviewer_note: string | null;
  submitted_at: string;
  resolved_at: string | null;
};