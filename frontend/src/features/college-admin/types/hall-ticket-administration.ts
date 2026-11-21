import type { ExaminationRegistrationSubNavItem } from "@/features/college-admin/types/examination-registration-shared";
import type { PoliciesPagination } from "@/features/college-admin/types/institution";

export type HallTicketAdministrationPageQuery = {
  page?: number;
  session_id?: string;
};

export type HallTicketAdministrationRow = {
  hall_ticket_id: string;
  student_name: string;
  register_number: string;
  papers_count: number;
  generated_at_label: string;
  released_at_label: string;
  status_label: string;
  status_tone: string;
};

export type HallTicketAdministrationPage = {
  page_title: string;
  page_subtitle: string;
  generate_all_label: string;
  release_label: string;
  sub_nav: ExaminationRegistrationSubNavItem[];
  scope_indicator_label: string;
  updated_at_label: string;
  kpis: { key: string; label: string; value: string; hint_line: string; hint_tone: string }[];
  hall_tickets_section_title: string;
  hall_tickets_count_label: string;
  table_headers: string[];
  ticket_rows: HallTicketAdministrationRow[];
  showing_label: string;
  pagination: PoliciesPagination;
  selected_session_id: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};