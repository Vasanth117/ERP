import type { InstitutionFieldOption } from "@/features/college-admin/types/institution";
import type { PoliciesPagination } from "@/features/college-admin/types/all-departments-list";

export type DepartmentStatusHistoryEventRow = {
  event_id: string;
  department_id: string;
  event_label: string;
  department_label: string;
  by_label: string;
  date_label: string;
  status_code: string;
  status_label: string;
  status_tone: string;
};

export type DepartmentStatusHistoryStatusSummaryItem = {
  key: string;
  title: string;
  subtitle: string;
  count: number;
  badge_tone: string;
  detail_count: number | null;
};

export type DepartmentStatusHistoryTimelineItem = {
  event_id: string;
  title: string;
  date_label: string;
  tone: string;
  nested_status_label: string | null;
};

export type DepartmentStatusHistoryPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  since_year_filter_label: string;
  department_filter_label: string;
  change_type_filter_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  since_year_options: InstitutionFieldOption[];
  department_options: InstitutionFieldOption[];
  change_type_options: InstitutionFieldOption[];
  selected_since_year: string;
  selected_department_id: string;
  selected_change_type: string;
  table_headers: string[];
  events: DepartmentStatusHistoryEventRow[];
  pagination: PoliciesPagination;
  showing_label: string;
  status_summary_title: string;
  status_summary_items: DepartmentStatusHistoryStatusSummaryItem[];
  timeline_section_title: string;
  selected_timeline_department_id: string;
  timeline_items: DepartmentStatusHistoryTimelineItem[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};