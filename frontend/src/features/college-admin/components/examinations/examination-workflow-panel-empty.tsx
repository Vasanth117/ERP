"use client";

import Link from "next/link";

import type { ErpIconName } from "@/components/icons/erp/names";
import { Button } from "@/components/ui/button";
import { CollegeAdminPanelEmptyState } from "@/features/college-admin/components/ui/dashboard-panel-ui";
import type { ExaminationWorkflowEmptyState } from "@/features/college-admin/types/examination-workflow-empty";
import { cn } from "@/lib/utils";
import { buttonVariants } from "@/components/ui/button";

const INLINE_ACTION_KEYS = new Set(["regenerate_timetable", "auto_allocate_seating"]);

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
      <Button
        type="button"
        className="h-9 bg-[#245dd8] text-xs font-medium hover:bg-[#1f4fb8]"
        disabled={primaryDisabled}
        onClick={() => onInlineAction(state.primary_action_key!)}
      >
        {state.primary_action_label}
      </Button>
    ) : state.primary_action_href ? (
      <Link
        href={state.primary_action_href}
        className={cn(buttonVariants({ className: "h-9 bg-[#245dd8] text-xs font-medium hover:bg-[#1f4fb8]" }))}
      >
        {state.primary_action_label}
      </Link>
    ) : null;

  const secondaryAction =
    state.secondary_action_href && state.secondary_action_label ? (
      <Link
        href={state.secondary_action_href}
        className={cn(buttonVariants({ variant: "outline", className: "h-9 border-[#dce3ec] text-xs font-medium" }))}
      >
        {state.secondary_action_label}
      </Link>
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