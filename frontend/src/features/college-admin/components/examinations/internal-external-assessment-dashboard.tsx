"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { ExaminationCreationWorkflowHeader, useExaminationWorkflowContinue } from "@/features/college-admin/components/examinations/examination-creation-workflow-header";
import { ExaminationWorkflowPanelEmpty } from "@/features/college-admin/components/examinations/examination-workflow-panel-empty";
import { ExaminationRegistrationSubNav } from "@/features/college-admin/components/examinations/examination-registration-sub-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useInternalExternalAssessmentPage, useSaveInternalExternalAssessment } from "@/features/college-admin/hooks/use-internal-external-assessment";
import { cn } from "@/lib/utils";


export function InternalExternalAssessmentDashboard() {
  const searchParams = useSearchParams();
  const sessionId = useMemo(() => searchParams.get("session_id") ?? undefined, [searchParams]);
  const continueTo = useExaminationWorkflowContinue();

  const { data, isLoading, isError, error, refetch } = useInternalExternalAssessmentPage({ session_id: sessionId });
  const save = useSaveInternalExternalAssessment();
  const [moderation, setModeration] = useState("");
  const [passMark, setPassMark] = useState("");

  useEffect(() => {
    if (data) {
      setModeration(data.selected_moderation_range);
      setPassMark(data.selected_pass_mark_percent);
    }
  }, [data?.selected_moderation_range, data?.selected_pass_mark_percent, data]);

  const persist = async (advance: boolean) => {
    if (!data?.selected_session_id) {
      toast.error("Open this step from the examination creation flow with a session selected.");
      return;
    }
    if (!data.selected_config_id && !advance) {
      toast.success("Draft saved");
      return;
    }
    if (!data.selected_config_id && advance) {
      continueTo(data.continue_href);
      return;
    }
    try {
      const result = await save.mutateAsync({
        session_id: data.selected_session_id,
        config_id: data.selected_config_id,
        moderation_range: moderation,
        pass_mark_percent: passMark,
        advance_workflow: advance,
      });
      if (advance) {
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
      <ExaminationCreationWorkflowHeader
        pageTitle={data?.page_title ?? "Internal & External Assessment"}
        pageSubtitle={data?.page_subtitle ?? "Weightage and moderation"}
        backHref={data?.back_href ?? "/college-admin/examinations/examination-configuration"}
        saveDraftLabel={data?.save_draft_label}
        continueLabel={data?.continue_label}
        workflowSteps={data?.workflow_steps}
        sessionId={data?.selected_session_id || sessionId}
        saving={save.isPending}
        continuing={save.isPending}
        saveDisabled={!data}
        onSaveDraft={() => void persist(false)}
        onContinue={() => void persist(true)}
      />

      {data?.sub_nav?.length ? <ExaminationRegistrationSubNav items={data.sub_nav} /> : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <div className="grid gap-5 lg:grid-cols-[1fr_minmax(14rem,20rem)]">
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.assessment_pattern_section_title}</h3>
              </div>
              {data.component_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[28rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.table_headers.map((header, index) => (
                          <th key={header} className={cn("pb-3 font-medium", index === 0 ? "pl-5 pr-3" : "pr-3", index === data.table_headers.length - 1 ? "pr-5" : "")}>
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.component_rows.map((row) => (
                        <tr key={row.component_id}>
                          <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">{row.component_label}</td>
                          <td className="py-3 pr-3 tabular-nums">{row.weight_label}</td>
                          <td className="py-3 pr-3 tabular-nums">{row.max_marks_label}</td>
                          <td className="py-3 pr-5 text-[#6b7280]">{row.source_label}</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="border-t border-[#f1f5f9]">
                        <td className="pl-5 py-3 font-semibold text-[#111827]">{data.total_weight_label}</td>
                        <td colSpan={3} />
                      </tr>
                    </tfoot>
                  </table>
                </div>
              ) : data.panel_empty_state ? (
                <ExaminationWorkflowPanelEmpty state={data.panel_empty_state} />
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
                  disabled={!data.selected_config_id}
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
                  disabled={!data.selected_config_id}
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