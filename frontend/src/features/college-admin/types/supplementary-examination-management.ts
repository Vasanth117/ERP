import type { ExaminationRegistrationSubNavItem } from "@/features/college-admin/types/examination-registration-shared";
import type { PoliciesPagination } from "@/features/college-admin/types/institution";

export type SupplementaryExaminationManagementPageQuery = {
  page?: number;
  session_id?: string;
};

export type SupplementaryArrearSubjectRow = {
  course_code: string;
  subject_label: string;
  students_count: number;
  date_label: string;
  hall_label: string;
};

export type SupplementaryExaminationManagementPage = {
  page_title: string;
  page_subtitle: string;
  create_session_label: string;
  create_session_href: string;
  sub_nav: ExaminationRegistrationSubNavItem[];
  eligible_hint_label: string;
  arrear_subjects_section_title: string;
  table_headers: string[];
  arrear_subject_rows: SupplementaryArrearSubjectRow[];
  kpis: { key: string; label: string; value: string; hint_line: string; hint_tone: string }[];
  showing_label: string;
  pagination: PoliciesPagination;
  selected_session_id: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};