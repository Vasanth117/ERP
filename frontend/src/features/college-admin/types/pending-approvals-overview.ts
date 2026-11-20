import type { DashboardDateRange } from "@/features/college-admin/types/dashboard";

export type PendingApprovalsOverviewQuery = {
  range?: DashboardDateRange;
  module_key?: string;
  requester_id?: string;
};

export type PendingApprovalOverviewKpi = {
  awaiting_action: number;
  modules_with_pending: number;
  overdue_count: number;
  overdue_sla_days: number;
  approved_this_week: number;
  avg_turnaround_days: number | null;
  escalated_to_college_admin: number;
};

export type PendingApprovalQueueRow = {
  reference_id: string;
  request_code: string;
  title: string;
  module_key: string;
  module_label: string;
  requested_by_label: string;
  requester_user_id: string | null;
  submitted_at: string;
  submitted_label: string;
  sla_key: string;
  sla_label: string;
  overdue_days: number | null;
  review_resource_type: string;
  review_resource_id: string;
};

export type PendingApprovalByModuleItem = {
  module_key: string;
  module_label: string;
  count: number;
};

export type PendingApprovalEscalationItem = {
  escalation_id: string;
  title: string;
  escalated_by_label: string;
  age_days: number;
  priority_key: string;
  priority_label: string;
};

export type PendingApprovalRecentDecisionItem = {
  event_id: string;
  title: string;
  decision_key: string;
  decision_label: string;
  decided_at: string;
  detail: string | null;
};

export type PendingApprovalModuleFilterOption = {
  module_key: string;
  module_label: string;
};

export type PendingApprovalRequesterFilterOption = {
  user_id: string;
  label: string;
};

export type PendingApprovalsOverview = {
  filters: {
    date_range: DashboardDateRange | null;
    module_key: string | null;
    requester_id: string | null;
  };
  scope_label: string;
  kpis: PendingApprovalOverviewKpi;
  queue_rows: PendingApprovalQueueRow[];
  queue_total: number;
  queue_limit: number;
  pending_by_module: PendingApprovalByModuleItem[];
  pending_by_module_max: number;
  escalations: PendingApprovalEscalationItem[];
  recently_decided: PendingApprovalRecentDecisionItem[];
  module_filter_options: PendingApprovalModuleFilterOption[];
  requester_filter_options: PendingApprovalRequesterFilterOption[];
  generated_at: string;
};