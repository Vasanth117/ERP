import type { HrDashboardLeaveRow } from "@/features/college-admin/types/hr-dashboard";
import type { HrRecruitmentPagination, HrRecruitmentSubNavItem } from "@/features/college-admin/types/hr-recruitment";
import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type HrEmployeeAttendanceTableRow = {
  employee_user_id: string;
  employee_name: string;
  department_label: string;
  present_count: number;
  leave_count: number;
  absent_count: number;
  attendance_rate_pct: number | null;
};

export type HrEmployeeAttendancePage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  sub_nav: HrRecruitmentSubNavItem[];
  kpis: UserDashboardKpi[];
  attendance_table_title: string;
  attendance_table_headers: string[];
  attendance_rows: HrEmployeeAttendanceTableRow[];
  table_footer_label: string;
  table_pagination: HrRecruitmentPagination;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type HrLeaveManagementPage = {
  page_title: string;
  page_subtitle: string;
  leave_policy_label: string;
  leave_policy_href: string;
  sub_nav: HrRecruitmentSubNavItem[];
  kpis: UserDashboardKpi[];
  applications_section_title: string;
  table_headers: string[];
  application_rows: HrDashboardLeaveRow[];
  showing_label: string;
  pagination: HrRecruitmentPagination;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type HrLeaveApprovalStep = {
  key: string;
  label: string;
  status_label: string;
  tone: string;
};

export type HrLeaveApprovalPage = {
  page_title: string;
  page_subtitle: string;
  selected_leave_request_id: string | null;
  back_href: string;
  back_label: string;
  return_label: string;
  return_href: string;
  reject_label: string;
  approve_label: string;
  application_card_title: string;
  employee_field_label: string;
  employee_label: string;
  leave_type_field_label: string;
  leave_type_label: string;
  dates_field_label: string;
  dates_label: string;
  balance_after_field_label: string;
  balance_after_label: string;
  cover_field_label: string;
  cover_label: string;
  decision_card_title: string;
  decision_field_label: string;
  decision_required: boolean;
  decision_options: { value: string; label: string }[];
  selected_decision: string;
  remarks_field_label: string;
  remarks_placeholder: string;
  remarks_value: string;
  approval_timeline_title: string;
  approval_steps: HrLeaveApprovalStep[];
  can_decide: boolean;
  decide_blocked_message: string | null;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type HrAttendanceLeavePageQuery = {
  page?: number;
  page_size?: number;
};

export type HrLeaveDecisionPayload = {
  leave_request_id: string;
  decision: "approved" | "rejected";
  note?: string;
};