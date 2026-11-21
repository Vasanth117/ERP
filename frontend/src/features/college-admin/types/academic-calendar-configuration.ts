import type { YearsSemestersSubNavItem } from "@/features/college-admin/types/academic-year-management";
import type { InstitutionFieldMeta, InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type AcademicCalendarViewTab = {
  key: string;
  label: string;
  active: boolean;
};

export type AcademicCalendarEventTableRow = {
  event_id: string;
  title: string;
  date_label: string;
  type_label: string;
  audience_label: string;
  status_label: string;
  status_tone: string;
};

export type AcademicCalendarTypeStatRow = {
  type_label: string;
  count: number;
  bar_percent: number;
};

export type AcademicCalendarAddEventForm = {
  title_meta: InstitutionFieldMeta;
  title_placeholder: string;
  type_meta: InstitutionFieldMeta;
  type_options: InstitutionFieldOption[];
  type_default_value: string;
  from_meta: InstitutionFieldMeta;
  to_meta: InstitutionFieldMeta;
  audience_meta: InstitutionFieldMeta;
  audience_options: InstitutionFieldOption[];
  audience_default_value: string;
  submit_label: string;
};

export type AcademicCalendarPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type AcademicCalendarConfigurationPage = {
  page_title: string;
  page_subtitle: string;
  publish_button_label: string;
  add_event_button_label: string;
  can_publish: boolean;
  primary_calendar_id: string | null;
  active_view: string;
  view_tabs: AcademicCalendarViewTab[];
  list_panel_title: string;
  table_headers: string[];
  event_rows: AcademicCalendarEventTableRow[];
  year_event_count_label: string;
  pagination: AcademicCalendarPagination;
  add_event_form: AcademicCalendarAddEventForm;
  type_stats_title: string;
  type_stats: AcademicCalendarTypeStatRow[];
  selected_academic_year_id: string;
  selected_term_id: string | null;
  sub_nav: YearsSemestersSubNavItem[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type AcademicCalendarAddEventPayload = {
  academic_year_id: string;
  title: string;
  event_type: string;
  from_date: string;
  to_date?: string | null;
  audience: string;
};

export type AcademicCalendarPublishPayload = {
  academic_year_id: string;
  calendar_id?: string | null;
};