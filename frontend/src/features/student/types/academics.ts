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

export type AcademicDetails = {
  admission: AdmissionInfo;
  enrollment_status: EnrollmentStatus;
  department_programme: DepartmentProgramme;
  current_enrollments: EnrollmentLine[];
  academic_record: AcademicEligibility | null;
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