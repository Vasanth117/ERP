import type { ExaminationDashboardSessionRow } from "@/features/college-admin/types/examination-dashboard";
import type { PoliciesPagination } from "@/features/college-admin/types/institution";

export type ExaminationSessionManagementPageQuery = {
  page?: number;
};

export type ExaminationSessionManagementPage = {
  page_title: string;
  page_subtitle: string;
  create_session_label: string;
  create_session_href: string;
  sessions_section_title: string;
  sessions_count_label: string;
  table_headers: string[];
  session_rows: ExaminationDashboardSessionRow[];
  showing_label: string;
  pagination: PoliciesPagination;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};