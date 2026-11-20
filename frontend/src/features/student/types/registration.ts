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