"use client";

import { CollegeAdminModulePageHeading } from "@/features/college-admin/components/layout/college-admin-module-page-heading";
import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import Link from "next/link";
import { useState } from "react";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import { CollegeAdminPanelChromeFooter } from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAttendanceRulesPoliciesPage,
  useSaveAttendanceInstitutionalPolicy,
} from "@/features/college-admin/hooks/use-attendance-configuration";
import type { AttendanceRulesPolicyRow } from "@/features/college-admin/types/attendance-configuration";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "text-[#047857]",
    muted: "text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    muted: "bg-[#9ca3af]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-[13px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}

type PolicyDraft = {
  policy_key?: string | null;
  title: string;
  value_label: string;
  applies_to_label: string;
  is_active: boolean;
};

const EMPTY_DRAFT: PolicyDraft = {
  policy_key: null,
  title: "",
  value_label: "",
  applies_to_label: "",
  is_active: true,
};

function PolicyEditorPanel({
  open,
  draft,
  onChange,
  onClose,
  onSave,
  saving,
  title,
}: {
  open: boolean;
  draft: PolicyDraft;
  onChange: (next: PolicyDraft) => void;
  onClose: () => void;
  onSave: () => void;
  saving: boolean;
  title: string;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4" role="dialog" aria-modal="true">
      <div className="w-full max-w-md rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-lg">
        <h3 className="text-[16px] font-semibold text-[#111827]">{title}</h3>
        <div className="mt-4 space-y-3">
          <div>
            <Label htmlFor="policy-title" className="text-[13px]">
              Policy name
            </Label>
            <Input
              id="policy-title"
              value={draft.title}
              onChange={(e) => onChange({ ...draft, title: e.target.value })}
              className="mt-1 h-9 border-[#dce3ec] text-[13px]"
            />
          </div>
          <div>
            <Label htmlFor="policy-value" className="text-[13px]">
              Value
            </Label>
            <Input
              id="policy-value"
              value={draft.value_label}
              onChange={(e) => onChange({ ...draft, value_label: e.target.value })}
              className="mt-1 h-9 border-[#dce3ec] text-[13px]"
            />
          </div>
          <div>
            <Label htmlFor="policy-applies" className="text-[13px]">
              Applies to
            </Label>
            <Input
              id="policy-applies"
              value={draft.applies_to_label}
              onChange={(e) => onChange({ ...draft, applies_to_label: e.target.value })}
              className="mt-1 h-9 border-[#dce3ec] text-[13px]"
            />
          </div>
          <label className="flex items-center gap-2 text-[13px] text-[#374151]">
            <input
              type="checkbox"
              checked={draft.is_active}
              onChange={(e) => onChange({ ...draft, is_active: e.target.checked })}
              className="size-4 rounded border-[#dce3ec]"
            />
            Active policy
          </label>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <Button type="button" variant="outline" className="h-9 text-xs" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button type="button" className="h-9 bg-[#245dd8] text-xs text-white" disabled={saving} onClick={onSave}>
            Save policy
          </Button>
        </div>
      </div>
    </div>
  );
}

export function AttendanceRulesPoliciesDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = { page, page_size: 4 };
  const { data, isLoading, isError, error, refetch } = useAttendanceRulesPoliciesPage(queryParams);
  const savePolicy = useSaveAttendanceInstitutionalPolicy(queryParams);

  const [editorOpen, setEditorOpen] = useState(false);
  const [draft, setDraft] = useState<PolicyDraft>(EMPTY_DRAFT);

  const openCreate = () => {
    setDraft(EMPTY_DRAFT);
    setEditorOpen(true);
  };

  const openEdit = (row: AttendanceRulesPolicyRow) => {
    setDraft({
      policy_key: row.row_key,
      title: row.policy_title,
      value_label: row.value_label,
      applies_to_label: row.applies_to_label,
      is_active: row.status_tone === "success",
    });
    setEditorOpen(true);
  };

  const handleSavePolicy = () => {
    if (!draft.title.trim() || !draft.value_label.trim()) {
      toast.error("Policy name and value are required");
      return;
    }
    savePolicy.mutate(
      {
        policy_key: draft.policy_key,
        title: draft.title.trim(),
        value_label: draft.value_label.trim(),
        applies_to_label: draft.applies_to_label.trim() || "All",
        is_active: draft.is_active,
      },
      {
        onSuccess: () => {
          toast.success(draft.policy_key ? "Policy updated" : "Policy added");
          setEditorOpen(false);
        },
        onError: onCollegeAdminMutationError,
      },
    );
  };

  return (
    <CollegeAdminModulePageLayout figmaFrame="159:10121">
      <CollegeAdminModulePageHeading title={data?.page_title ?? "Attendance Rules & Policies"} subtitle={data?.page_subtitle ?? "—"} actions={<><Link
            href={data?.configuration_href ?? "/college-admin/attendance/attendance-configuration"}
            className={cn(buttonVariants({ variant: "outline" }), "h-9 text-xs")}
          >
            {data?.back_label ?? "View configuration"}
          </Link>
          <Link
            href={data?.configuration_edit_href ?? "/college-admin/attendance/attendance-configuration?edit=1"}
            className={cn(buttonVariants({ variant: "outline" }), "h-9 text-xs")}
          >
            {data?.edit_marking_settings_label ?? "Edit marking settings"}
          </Link>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs text-white hover:bg-[#1f4fb8]"
            onClick={openCreate}
          >
            <CollegeAdminPlusActionLabel label={data?.add_policy_label ?? "Add policy"} />
          </Button></>} />

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <div className="border-b border-[#f1f5f9] px-5 py-3.5">
              <h3 className="text-[14px] font-semibold text-[#111827]">{data.policies_section_title}</h3>
            </div>
            {data.policy_rows.length ? (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[48rem] text-left text-[13px]">
                  <thead>
                    <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                      {data.policies_table_headers.map((header) => (
                        <th key={header} className="px-5 py-3 font-medium">
                          {header}
                        </th>
                      ))}
                      <th className="px-5 py-3 font-medium">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f1f5f9]">
                    {data.policy_rows.map((row) => (
                      <tr key={row.row_key} className="text-[#111827]">
                        <td className="px-5 py-3.5 font-semibold">{row.policy_title}</td>
                        <td className="px-5 py-3.5">{row.value_label}</td>
                        <td className="px-5 py-3.5 text-[#6b7280]">{row.applies_to_label}</td>
                        <td className="px-5 py-3.5 text-[#6b7280]">{row.effective_label}</td>
                        <td className="px-5 py-3.5">
                          <StatusPill label={row.status_label} tone={row.status_tone} />
                        </td>
                        <td className="px-5 py-3.5">
                          <Button
                            type="button"
                            variant="ghost"
                            className="h-8 text-xs text-[#245dd8]"
                            onClick={() => openEdit(row)}
                          >
                            {data.edit_policy_label ?? "Edit"}
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="px-5 py-8 text-center text-[13px] text-[#6b7280]">
                No policies yet. Use Add policy to create one.
              </p>
            )}
            <div className="flex items-center justify-between border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
              <span>{data.policies_table_footer_label}</span>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="rounded px-2 py-0.5 hover:bg-[#f3f4f6] disabled:opacity-40"
                >
                  Prev
                </button>
                <button
                  type="button"
                  onClick={() => setPage((p) => p + 1)}
                  className="rounded px-2 py-0.5 hover:bg-[#f3f4f6]"
                >
                  Next
                </button>
              </div>
            </div>
          </section>
        ) : null}
      </QueryState>

      {data ? (
        <CollegeAdminPanelChromeFooter className="rounded-xl border border-[#e8ecf2] bg-[#fafbfc]">
          <span>{data.footer_disclaimer}</span>
          <span className="shrink-0 tabular-nums">{data.footer_snapshot_label}</span>
        </CollegeAdminPanelChromeFooter>
      ) : null}

      <PolicyEditorPanel
        open={editorOpen}
        draft={draft}
        onChange={setDraft}
        onClose={() => setEditorOpen(false)}
        onSave={handleSavePolicy}
        saving={savePolicy.isPending}
        title={draft.policy_key ? "Edit policy" : "Add policy"}
      />
    </CollegeAdminModulePageLayout>
  );
}