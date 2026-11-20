import type { DashboardDateRange } from "@/features/college-admin/types/dashboard";

export type RecentActivitiesOverviewQuery = {
  range?: DashboardDateRange;
  module_key?: string;
  user_id?: string;
  feed_offset?: number;
  feed_limit?: number;
};

export type RecentActivitiesOverviewKpi = {
  actions_count: number;
  actions_kpi_label: string;
  actions_period_label: string;
  actions_vs_daily_avg_pct: number | null;
  active_administrators: number;
  active_role_count: number;
  records_changed: number;
  records_changed_hint: string;
  failed_actions: number;
  failed_actions_hint: string;
};

export type RecentActivityFeedRow = {
  activity_id: string;
  title: string;
  module_key: string;
  module_label: string;
  performed_by_label: string;
  actor_user_id: string | null;
  occurred_at: string;
  time_label: string;
  result_key: string;
  result_label: string;
};

export type RecentActivityByModuleItem = {
  module_key: string;
  module_label: string;
  count: number;
};

export type RecentActivityTopPerformerItem = {
  performer_key: string;
  performer_label: string;
  module_label: string;
  action_count: number;
};

export type RecentActivityFollowUpItem = {
  item_key: string;
  title: string;
  detail: string | null;
  action_key: string;
  action_label: string;
  resource_type: string | null;
  resource_id: string | null;
};

export type RecentActivitiesOverview = {
  filters: {
    anchor_date: string | null;
    date_range: DashboardDateRange | null;
    module_key: string | null;
    user_id: string | null;
    feed_offset: number;
    feed_limit: number;
  };
  scope_label: string;
  kpis: RecentActivitiesOverviewKpi;
  feed_rows: RecentActivityFeedRow[];
  feed_total: number;
  feed_limit: number;
  feed_offset: number;
  activity_by_module: RecentActivityByModuleItem[];
  activity_by_module_max: number;
  top_performers: RecentActivityTopPerformerItem[];
  follow_ups: RecentActivityFollowUpItem[];
  module_filter_options: { module_key: string; module_label: string }[];
  user_filter_options: { user_id: string; label: string }[];
  generated_at: string;
};