import type { ExaminationRegistrationSubNavItem } from "@/features/college-admin/types/examination-registration-shared";
import type { PoliciesPagination } from "@/features/college-admin/types/institution";

export type StudentExamEligibilityPageQuery = {
  page?: number;
  session_id?: string;
};

export type StudentExamEligibilityTableRow = {
  student_name: string;
  register_number: string;
  reason_label: string;
  attendance_label: string;
  fee_status_label: string;
  fee_status_tone: string;
  decision_label: string;
  decision_tone: string;
};

export type StudentExamEligibilityPage = {
  page_title: string;
  page_subtitle: string;
  rerun_check_label: string;
  sub_nav: ExaminationRegistrationSubNavItem[];
  scope_indicator_label: string;
  updated_at_label: string;
  kpis: { key: string; label: string; value: string; hint_line: string; hint_tone: string }[];
  ineligible_section_title: string;
  ineligible_count_label: string;
  table_headers: string[];
  ineligible_rows: StudentExamEligibilityTableRow[];
  showing_label: string;
  pagination: PoliciesPagination;
  selected_session_id: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};