"use client";

import type { ErpIconName } from "@/components/icons/erp/names";
import {
  CollegeAdminPrimaryButton,
  CollegeAdminPrimaryLink,
  CollegeAdminSecondaryLink,
} from "@/features/college-admin/components/ui/college-admin-action-button";
import { CollegeAdminPanelEmptyState } from "@/features/college-admin/components/ui/dashboard-panel-ui";
import type { ExaminationWorkflowEmptyState } from "@/features/college-admin/types/examination-workflow-empty";

const INLINE_ACTION_KEYS = new Set(["regenerate_timetable", "auto_allocate_seating", "create_assessment_pattern"]);

export function ExaminationWorkflowPanelEmpty({
  state,
  onInlineAction,
  primaryDisabled,
}: {
  state: ExaminationWorkflowEmptyState;
  onInlineAction?: (actionKey: string) => void;
  primaryDisabled?: boolean;
}) {
  const iconSlug = (state.icon_slug || "inbox") as ErpIconName;
  const primaryIsInline = state.primary_action_key && INLINE_ACTION_KEYS.has(state.primary_action_key);

  const primaryAction =
    primaryIsInline && onInlineAction ? (
      <CollegeAdminPrimaryButton disabled={primaryDisabled} onClick={() => onInlineAction(state.primary_action_key!)}>
        {state.primary_action_label}
      </CollegeAdminPrimaryButton>
    ) : state.primary_action_href ? (
      <CollegeAdminPrimaryLink href={state.primary_action_href}>{state.primary_action_label}</CollegeAdminPrimaryLink>
    ) : null;

  const secondaryAction =
    state.secondary_action_href && state.secondary_action_label ? (
      <CollegeAdminSecondaryLink href={state.secondary_action_href}>{state.secondary_action_label}</CollegeAdminSecondaryLink>
    ) : null;

  return (
    <CollegeAdminPanelEmptyState
      iconSlug={iconSlug}
      title={state.title}
      description={state.description}
      action={
        <>
          {primaryAction}
          {secondaryAction}
        </>
      }
    />
  );
}