import type { ExaminationRegistrationSubNavItem } from "@/features/college-admin/types/examination-registration-shared";

export type ExaminationHallSeatingManagementPageQuery = {
  page?: number;
  session_id?: string;
};

export type ExaminationHallSeatingHallRow = {
  room_id: string;
  hall_label: string;
  capacity: number;
  allocated_count: number;
  papers_count: number;
  status_label: string;
  status_tone: string;
};

export type ExaminationHallSeatingSeatUsageItem = {
  hall_label: string;
  allocated_count: number;
  capacity: number;
  usage_label: string;
  usage_percent: number;
};

export type ExaminationHallSeatingManagementPage = {
  page_title: string;
  page_subtitle: string;
  auto_allocate_label: string;
  confirm_label: string;
  sub_nav: ExaminationRegistrationSubNavItem[];
  halls_section_title: string;
  seat_usage_section_title: string;
  table_headers: string[];
  hall_rows: ExaminationHallSeatingHallRow[];
  seat_usage_items: ExaminationHallSeatingSeatUsageItem[];
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