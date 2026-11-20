import type { InstitutionFieldMeta, InstitutionFieldOption } from "@/features/college-admin/types/institution";
import type { PoliciesPagination } from "@/features/college-admin/types/institution";

export type AccountStatusSuspendFormValues = {
  user_id: string;
  reason_code: string;
  effective_from: string;
  review_date: string;
  notes: string;
};

export type AccountStatusTab = {
  key: string;
  label: string;
  count: number;
  active: boolean;
};

export type AccountStatusTableRow = {
  user_id: string;
  user_name: string;
  role_label: string;
  reason_label: string;
  since_label: string;
  review_label: string;
  review_tone: string;
  department_label: string;
  detail_href: string;
};

export type AccountStatusInfoCard = {
  key: string;
  title: string;
  description: string;
  icon_key: string;
};

export type AccountStatusPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  suspend_account_label: string;
  tabs: AccountStatusTab[];
  active_tab: string;
  table_headers: string[];
  table_rows: AccountStatusTableRow[];
  table_footer_label: string;
  pagination: PoliciesPagination;
  suspend_form_section_title: string;
  suspend_field_meta: InstitutionFieldMeta[];
  reason_options: InstitutionFieldOption[];
  user_options: InstitutionFieldOption[];
  suspend_form: AccountStatusSuspendFormValues;
  what_happens_title: string;
  what_happens_cards: AccountStatusInfoCard[];
  cancel_href: string;
  cancel_label: string;
  submit_suspend_label: string;
  footer_note: string;
  footer_snapshot_label: string;
  can_suspend: boolean;
  generated_at: string;
};

export type AccountStatusSuspendResult = {
  page: AccountStatusPage;
  message: string;
};