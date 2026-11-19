export type DashboardDateRange = "today" | "week" | "month" | "semester";

export type AcademicTermSummary = {
  academic_year_label: string | null;
  semester_label: string | null;
};

export type HeadcountStatistics = {
  total_students: number;
  active_students: number;
  faculty_count: number;
  employee_count: number;
  department_count: number;
  programme_count: number;
};

export type CollegeDashboardOverview = {
  filters: {
    anchor_date: string | null;
    date_range: DashboardDateRange;
    department_id: string | null;
    campus_id: string | null;
    academic_year_label: string | null;
  };
  academic_term: AcademicTermSummary;
  statistics: HeadcountStatistics;
  attendance: {
    sessions_submitted: number;
    pending_submissions: number;
    correction_requests_open: number;
  };
  examinations: {
    scheduled_exams: number;
    pending_evaluations: number;
    published_results: number;
  };
  finance: {
    collected_amount: number;
    outstanding_amount: number;
    open_demands: number;
    overdue_demands: number;
  };
  library_hostel: {
    catalog_items: number;
    active_circulation: number;
    open_fines: number;
    hostel_allocations: number;
    pending_hostel_applications: number;
  };
  pending_approval_count: number;
  unresolved_support_count: number;
  upcoming_events: Record<string, unknown>[];
  notifications: {
    title: string;
    message: string;
    severity: string;
    created_at: string;
  }[];
  integration_health: {
    provider_code: string;
    status: string;
    last_check_at: string | null;
    detail: string | null;
  }[];
};

export type OperationalSummariesRead = {
  attendance: CollegeDashboardOverview["attendance"];
  examinations: CollegeDashboardOverview["examinations"];
  finance: CollegeDashboardOverview["finance"];
  library_hostel: CollegeDashboardOverview["library_hostel"];
  integration_health: CollegeDashboardOverview["integration_health"];
};

export type ActivitySummary = {
  activity_id: string;
  category: string;
  title: string;
  actor_label: string | null;
  occurred_at: string;
  reference_id: string | null;
};

export type PendingApprovalItem = {
  category: string;
  title: string;
  submitted_at: string;
  reference_id: string;
  department_id: string | null;
  campus_id: string | null;
};

export type ApiPage<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};