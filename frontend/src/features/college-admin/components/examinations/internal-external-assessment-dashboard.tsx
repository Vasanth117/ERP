"use client";

import { useEffect, useState } from "react";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { useExaminationWorkflowContinue } from "@/features/college-admin/components/examinations/examination-creation-workflow-header";
import { ExaminationWorkflowOrPageHeading } from "@/features/college-admin/components/examinations/examination-workflow-or-page-heading";
import { useExaminationCreationWorkflowVisible } from "@/features/college-admin/context/examination-creation-flow-context";
import { ExaminationWorkflowPanelEmpty } from "@/features/college-admin/components/examinations/examination-workflow-panel-empty";
import { ExaminationRegistrationSubNav } from "@/features/college-admin/components/examinations/examination-registration-sub-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useExaminationCreationSessionId } from "@/features/college-admin/hooks/use-examination-creation-flow";
import { AssessmentPatternEditor } from "@/features/college-admin/components/examinations/assessment-pattern-editor";
import {
  useCreateInternalExternalAssessmentPattern,
  useInternalExternalAssessmentPage,
  useSaveInternalExternalAssessment,
} from "@/features/college-admin/hooks/use-internal-external-assessment";
import type { InternalExternalAssessmentComponentDraft } from "@/features/college-admin/types/internal-external-assessment";


export function InternalExternalAssessmentDashboard() {
  const sessionId = useExaminationCreationSessionId();
  const inCreationModal = useExaminationCreationWorkflowVisible();
  const continueTo = useExaminationWorkflowContinue();

  const { data, isLoading, isError, error, refetch } = useInternalExternalAssessmentPage({ session_id: sessionId });
  const save = useSaveInternalExternalAssessment();
  const createPattern = useCreateInternalExternalAssessmentPattern();
  const effectiveSessionId = (data?.selected_session_id || sessionId || "").trim();
  const [moderation, setModeration] = useState("");
  const [passMark, setPassMark] = useState("");
  const [componentDrafts, setComponentDrafts] = useState<InternalExternalAssessmentComponentDraft[]>([]);

  useEffect(() => {
    if (data) {
      setModeration(data.selected_moderation_range);
      setPassMark(data.selected_pass_mark_percent);
      if (data.component_drafts?.length) {
        setComponentDrafts(data.component_drafts.map((row) => ({ ...row })));
      } else if (!data.component_rows.length) {
        setComponentDrafts([]);
      }
    }
  }, [data?.selected_moderation_range, data?.selected_pass_mark_percent, data?.component_drafts, data?.component_rows.length, data]);

  const totalWeight = componentDrafts.reduce((sum, row) => sum + (Number(row.weight_percent) || 0), 0);
  const weightBalanced = Math.abs(totalWeight - 100) < 0.05;
  const hasPattern = Boolean(data?.selected_config_id) || componentDrafts.length > 0;

  const handleCreateAssessmentPattern = () => {
    if (!effectiveSessionId) {
      toast.error("Select an examination session first.");
      return;
    }
    createPattern.mutate(effectiveSessionId, {
      onSuccess: (result) => {
        void refetch();
        if (result.component_rows.length) {
          toast.success("Assessment pattern created.");
        } else {
          toast.message("Pattern saved — add components or try again.");
        }
      },
      onError: onCollegeAdminMutationError,
    });
  };

  const persist = async (advance: boolean) => {
    if (!data) return;
    if (!data.selected_session_id && !sessionId) {
      toast.error("Select an examination session to continue.");
      return;
    }
    if (!componentDrafts.length && !data.selected_config_id) {
      toast.error("Create or add at least one assessment component.");
      return;
    }
    if (advance && !weightBalanced) {
      toast.error("Component weights must total 100% before continuing.");
      return;
    }
    if (advance && componentDrafts.some((row) => !row.name.trim())) {
      toast.error("Name every assessment component before continuing.");
      return;
    }
    try {
      const result = await save.mutateAsync({
        session_id: data.selected_session_id || sessionId || "",
        config_id: data.selected_config_id ?? "",
        moderation_range: moderation,
        pass_mark_percent: passMark,
        components: componentDrafts,
        advance_workflow: advance,
      });
      if (result.component_drafts?.length) {
        setComponentDrafts(result.component_drafts.map((row) => ({ ...row })));
      }
      if (advance) {
        if (!result.continue_href) {
          toast.error("Unable to continue to the next step.");
          return;
        }
        toast.success("Step saved — continue to next stage");
        continueTo(result.continue_href);
      } else {
        toast.success("Draft saved");
      }
    } catch (e) {
      onCollegeAdminMutationError(e as Error & { details?: unknown });
    }
  };

  return (
    <div className="space-y-5" data-figma-frame="159:14123">
      <ExaminationWorkflowOrPageHeading
        pageTitle={data?.page_title ?? "Internal & External Assessment"}
        pageSubtitle={data?.page_subtitle ?? "Weightage and moderation"}
        backHref={data?.back_href ?? "/college-admin/examinations/examination-configuration"}
        saveDraftLabel={data?.save_draft_label}
        continueLabel={data?.continue_label}
        workflowSteps={inCreationModal ? data?.workflow_steps : undefined}
        sessionId={data?.selected_session_id || sessionId}
        busy={save.isPending || createPattern.isPending}
        controlsDisabled={isLoading || !data}
        continueEnabled={(data?.continue_enabled ?? true) && weightBalanced && hasPattern}
        onSaveDraft={() => void persist(false)}
        onContinue={() => void persist(true)}
      />

      {data?.sub_nav?.length && !sessionId ? <ExaminationRegistrationSubNav items={data.sub_nav} /> : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <div className="grid gap-5 lg:grid-cols-[1fr_minmax(14rem,20rem)]">
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.assessment_pattern_section_title}</h3>
              </div>
              {hasPattern ? (
                <AssessmentPatternEditor
                  components={componentDrafts}
                  assessmentTypeOptions={data.assessment_type_options ?? []}
                  sourceOptions={data.source_options ?? []}
                  addLabel={data.add_component_label ?? "Add component"}
                  onChange={setComponentDrafts}
                />
              ) : data.panel_empty_state ? (
                <ExaminationWorkflowPanelEmpty
                  state={data.panel_empty_state}
                  primaryDisabled={createPattern.isPending || !effectiveSessionId}
                  onInlineAction={(key) => {
                    if (key === "create_assessment_pattern") handleCreateAssessmentPattern();
                  }}
                />
              ) : (
                <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">No assessment pattern configured yet.</p>
              )}
            </section>

            <aside className="space-y-4 rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <h3 className="text-[14px] font-semibold text-[#111827]">{data.moderation_section_title}</h3>
              <label className="block text-[12px] font-medium text-[#6b7280]">
                {data.moderation_range_label}
                <select
                  className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]"
                  value={moderation}
                  onChange={(e) => setModeration(e.target.value)}
                  disabled={!hasPattern}
                >
                  {data.moderation_range_options.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-[12px] font-medium text-[#6b7280]">
                {data.pass_mark_label}
                <select
                  className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]"
                  value={passMark}
                  onChange={(e) => setPassMark(e.target.value)}
                  disabled={!hasPattern}
                >
                  {data.pass_mark_options.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </label>
            </aside>
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}