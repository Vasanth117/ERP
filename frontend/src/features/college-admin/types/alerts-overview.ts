export type AlertsOverviewKpi = {
  critical_count: number;
  critical_hint: string;
  warning_count: number;
  warning_hint: string;
  info_count: number;
  info_hint: string;
  resolved_today: number;
  resolved_hint: string;
  avg_resolution_hours: number | null;
};

export type DashboardAlertItem = {
  alert_id: string;
  severity_key: string;
  severity_label: string;
  title: string;
  summary: string | null;
  module_key: string;
  module_label: string;
  raised_at: string;
  time_label: string;
  action_key: string;
  action_label: string;
  action_href: string;
  is_read: boolean;
};

export type AlertsFeaturedBanner = {
  alert_id: string;
  title: string;
  summary: string | null;
  action_label: string;
  action_href: string;
};

export type DashboardAlertByModuleItem = {
  module_key: string;
  module_label: string;
  count: number;
};

export type AlertsDeliveryChannelItem = {
  channel_key: string;
  label: string;
  detail: string;
  enabled: boolean;
};

export type AlertsRuleItem = {
  rule_key: string;
  label: string;
  value_label: string;
};

export type AlertsOverview = {
  kpis: AlertsOverviewKpi;
  featured: AlertsFeaturedBanner | null;
  all_alerts: DashboardAlertItem[];
  alerts_total: number;
  alerts_by_module: DashboardAlertByModuleItem[];
  alerts_by_module_max: number;
  delivery_channels: AlertsDeliveryChannelItem[];
  alert_rules: AlertsRuleItem[];
  generated_at: string;
};