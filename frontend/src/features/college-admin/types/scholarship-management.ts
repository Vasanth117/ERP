import type {
  FinanceAidPagination,
  FinanceAidSubNavItem,
  FinanceAidUserDashboardKpi,
} from "@/features/college-admin/types/finance-aid-shared";

export type ScholarshipManagementPageQuery = {
  page?: number;
};

export type FinanceScholarshipTableRow = {
  scheme_label: string;
  category_label: string;
  students_label: string;
  awarded_label: string;
  applied_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type ScholarshipManagementPage = {
  page_title: string;
  page_subtitle: string;
  new_programme_label: string;
  new_programme_href: string;
  kpis: FinanceAidUserDashboardKpi[];
  sub_nav: FinanceAidSubNavItem[];
  scholarships_section_title: string;
  table_headers: string[];
  scholarship_rows: FinanceScholarshipTableRow[];
  list_count_label: string;
  showing_label: string;
  pagination: FinanceAidPagination;
  generated_at: string;
};