import type { InstitutionFieldMeta, InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type CommunicationCreateAnnouncementFormValues = {
  announcement_id: string;
  title: string;
  body: string;
  attachment_name: string;
  audience: string;
  department_scope: string;
  channels: string[];
  publish_timing: string;
  scheduled_for: string;
  pin_to_dashboard: boolean;
};

export type CommunicationCreateAnnouncementPage = {
  page_title: string;
  page_subtitle: string;
  back_href: string;
  back_label: string;
  cancel_label: string;
  save_draft_label: string;
  publish_label: string;
  message_section_title: string;
  audience_section_title: string;
  pin_to_dashboard_label: string;
  field_meta: InstitutionFieldMeta[];
  audience_options: InstitutionFieldOption[];
  department_options: InstitutionFieldOption[];
  channel_options: InstitutionFieldOption[];
  publish_options: InstitutionFieldOption[];
  form: CommunicationCreateAnnouncementFormValues;
  generated_at: string;
};