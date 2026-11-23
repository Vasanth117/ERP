export type ProgrammeDetailsSummaryRow = {
  label: string;
  value: string;
};

export type ProgrammeDetailsChecklistItem = {
  key: string;
  title: string;
  description: string;
  enabled: boolean;
};

export type ProgrammeDetailsLinkedItem = {
  key: string;
  title: string;
  description: string;
  href: string;
  icon_slug: string;
};

export type ProgrammeDetailsPage = {
  page_title: string;
  page_subtitle: string;
  programme_name: string;
  programme_code: string;
  status_label: string;
  status_tone: string;
  back_href: string;
  edit_note: string;
  summary_rows: ProgrammeDetailsSummaryRow[];
  description: string | null;
  checklist_title: string;
  checklist_items: ProgrammeDetailsChecklistItem[];
  linked_title: string;
  linked_items: ProgrammeDetailsLinkedItem[];
  generated_at: string;
};