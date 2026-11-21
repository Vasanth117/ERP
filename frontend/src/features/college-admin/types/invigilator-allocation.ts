import type { ExaminationRegistrationSubNavItem } from "@/features/college-admin/types/examination-registration-shared";

export type InvigilatorAllocationPageQuery = {
  page?: number;
  session_id?: string;
};

export type InvigilatorAllocationDutyRow = {
  duty_key: string;
  date_label: string;
  session_label: string;
  hall_label: string;
  invigilator_label: string;
  substitute_label: string;
  status_label: string;
  status_tone: string;
};

export type InvigilatorAllocationPage = {
  page_title: string;
  page_subtitle: string;
  auto_assign_label: string;
  publish_roster_label: string;
  sub_nav: ExaminationRegistrationSubNavItem[];
  duties_section_title: string;
  table_headers: string[];
  duty_rows: InvigilatorAllocationDutyRow[];
  showing_label: string;
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    page_numbers: number[];
    has_previous: boolean;
    has_next: boolean;
  };
  selected_session_id: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};