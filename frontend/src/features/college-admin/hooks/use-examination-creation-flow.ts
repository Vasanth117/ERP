"use client";

import { useSearchParams } from "next/navigation";
import { useMemo } from "react";

import { useExaminationCreationFlowOptional } from "@/features/college-admin/context/examination-creation-flow-context";
import type { ExaminationWorkflowStep } from "@/features/college-admin/types/examination-dashboard";

/** Session id for the active create-examination flow (modal) or ?session_id= on the URL. */
export function useExaminationCreationSessionId(): string | undefined {
  const flow = useExaminationCreationFlowOptional();
  const searchParams = useSearchParams();
  return useMemo(() => {
    if (flow?.isModalOpen && flow.sessionId) return flow.sessionId;
    const id = searchParams.get("session_id");
    return id && id.trim() ? id : undefined;
  }, [flow?.isModalOpen, flow?.sessionId, searchParams]);
}

export function examinationWorkflowStepSubtitle(
  steps: ExaminationWorkflowStep[] | undefined,
  activeKey: string | undefined,
  fallback?: string,
): string {
  if (!steps?.length || !activeKey) return fallback ?? "";
  const active = steps.find((step) => step.key === activeKey) ?? steps.find((step) => step.status === "active");
  if (!active) return fallback ?? "";
  const total = steps.length;
  return `Step ${active.step_number} of ${total} · ${active.label}`;
}