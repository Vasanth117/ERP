import type { ErpIconName } from "@/components/icons/erp/names";

export type ExaminationWorkflowEmptyState = {
  icon_slug: ErpIconName;
  title: string;
  description: string;
  primary_action_label: string;
  primary_action_href?: string | null;
  primary_action_key?: string | null;
  secondary_action_label?: string | null;
  secondary_action_href?: string | null;
};