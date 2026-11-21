import type { ExaminationRegistrationSubNavItem } from "@/features/college-admin/types/examination-registration-shared";

export type ResultProcessingPageQuery = {
  session_id?: string;
};

export type ResultProcessingPassBarRow = {
  programme_code: string;
  programme_label: string;
  pass_percent: number;
  pass_percent_label: string;
  bar_tone: string;
};

export type ResultProcessingPage = {
  page_title: string;
  page_subtitle: string;
  process_label: string;
  sub_nav: ExaminationRegistrationSubNavItem[];
  pass_chart_section_title: string;
  kpis: { key: string; label: string; value: string; hint_line: string; hint_tone: string }[];
  pass_by_programme: ResultProcessingPassBarRow[];
  selected_session_id: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};