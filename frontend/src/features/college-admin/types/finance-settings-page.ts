import type { InstitutionFieldMeta, InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type FinanceSettingsFormValues = {
  invoice_prefix: string;
  receipt_prefix: string;
  financial_year_start: string;
  refund_approver: string;
  late_fee_policy: string;
  default_payment_methods: string;
  confirm_online_backend: boolean;
  lock_posted_entries: boolean;
  allow_installment_plans: boolean;
};

export type FinanceSettingsToggleRule = {
  key: keyof FinanceSettingsFormValues;
  label: string;
  description: string;
  badge_label: string;
  enabled: boolean;
};

export type FinanceSettingsPage = {
  page_title: string;
  page_subtitle: string;
  cancel_label: string;
  save_label: string;
  configuration_section_title: string;
  controls_section_title: string;
  form: FinanceSettingsFormValues;
  field_meta: InstitutionFieldMeta[];
  field_options: Record<string, InstitutionFieldOption[]>;
  toggle_rules: FinanceSettingsToggleRule[];
  generated_at: string;
};