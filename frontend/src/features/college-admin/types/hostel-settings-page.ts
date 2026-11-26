import type { InstitutionFieldMeta, InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type HostelSettingsFormValues = {
  gate_closing_boys: string;
  gate_closing_girls: string;
  visiting_hours: string;
  security_deposit: string;
  outpass_approver: string;
  mess_plans: string;
  notify_guardian_on_outpass: boolean;
  block_check_in_unpaid_fees: boolean;
  allow_visitors_after_hours: boolean;
};

export type HostelSettingsToggleRule = {
  key: string;
  label: string;
  description?: string;
  badge_label?: string;
  enabled: boolean;
};

export type HostelSettingsPage = {
  page_title: string;
  page_subtitle: string;
  cancel_label: string;
  save_label: string;
  hostel_rules_section_title: string;
  controls_section_title: string;
  field_meta: InstitutionFieldMeta[];
  field_options: Record<string, InstitutionFieldOption[]>;
  form: HostelSettingsFormValues;
  toggle_rules: HostelSettingsToggleRule[];
  generated_at: string;
};