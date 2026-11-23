"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { CircleCheckIcon } from "@/components/icons/erp/generated/circle-check";
import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { SlidersHorizontalIcon } from "@/components/icons/erp/generated/sliders-horizontal";
import { TriangleAlertIcon } from "@/components/icons/erp/generated/triangle-alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  CollegeAdminOutlineButton,
  CollegeAdminOutlineLink,
  CollegeAdminPrimaryButton,
  collegeAdminActionLabel,
} from "@/features/college-admin/components/ui/college-admin-page-buttons";
import { OrganizationSetupEmptyState } from "@/features/college-admin/components/ui/organization-setup-empty-state";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useDepartmentHeadAssignmentPage,
  useSubmitDepartmentHeadAssignment,
} from "@/features/college-admin/hooks/use-department-head-assignment";
import type { DepartmentHeadAssignmentFormValues } from "@/features/college-admin/types/department-head-assignment";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    error: "bg-[#ef4444]",
    info: "bg-[#3b82f6]",
    muted: "bg-[#9ca3af]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}

function EligibilityBadge({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "border-[#a7f3d0] bg-[#ecfdf5] text-[#047857]",
    warning: "border-[#fed7aa] bg-[#fff7ed] text-[#c2410c]",
    error: "border-[#fecaca] bg-[#fef2f2] text-[#b91c1c]",
    muted: "border-[#e5e7eb] bg-[#f9fafb] text-[#6b7280]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("rounded-md border px-2 py-0.5 text-[11px] font-medium", styles[key])}>{label}</span>
  );
}

function isoToDateInput(iso: string) {
  if (!iso) return "";
  return iso.slice(0, 10);
}

export function DepartmentHeadAssignmentDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialDept = searchParams.get("departmentId") ?? "";

  const [page, setPage] = useState(1);
  const [selectedDepartmentId, setSelectedDepartmentId] = useState(initialDept);
  const [facultyUserId, setFacultyUserId] = useState("");
  const [formDraft, setFormDraft] = useState<DepartmentHeadAssignmentFormValues | null>(null);

  useEffect(() => {
    if (initialDept) setSelectedDepartmentId(initialDept);
  }, [initialDept]);

  const queryParams = useMemo(
    () => ({
      page,
      selected_department_id: selectedDepartmentId || undefined,
      faculty_user_id: facultyUserId || undefined,
    }),
    [page, selectedDepartmentId, facultyUserId],
  );

  const { data, isLoading, isError, error, refetch, isFetching } = useDepartmentHeadAssignmentPage(queryParams);
  const submit = useSubmitDepartmentHeadAssignment();

  useEffect(() => {
    if (!data?.form) return;
    setFormDraft((prev) => {
      if (prev && facultyUserId && prev.faculty_user_id === facultyUserId) {
        return prev;
      }
      return { ...data.form };
    });
    if (!facultyUserId && data.form.faculty_user_id) {
      setFacultyUserId(data.form.faculty_user_id);
    }
    if (data.selected_department_id && data.selected_department_id !== selectedDepartmentId) {
      setSelectedDepartmentId(data.selected_department_id);
    }
  }, [data, facultyUserId, selectedDepartmentId]);

  const form = formDraft ?? data?.form;
  const formInteractive = data?.form_interactive ?? false;
  const assignHeadEnabled = data?.assign_head_enabled ?? false;

  const updateForm = useCallback(
    (patch: Partial<DepartmentHeadAssignmentFormValues>) => {
      if (!formInteractive) return;
      setFormDraft((prev) => {
        const base = prev ?? data?.form;
        if (!base) return prev;
        return { ...base, ...patch };
      });
      if (patch.faculty_user_id !== undefined) {
        setFacultyUserId(patch.faculty_user_id);
      }
    },
    [data?.form, formInteractive],
  );

  const handleSelectDepartment = (departmentId: string) => {
    if (!assignHeadEnabled) return;
    setSelectedDepartmentId(departmentId);
    setFacultyUserId("");
    setFormDraft(null);
    setPage((current) => {
      const row = data?.table_rows.find((r) => r.department_id === departmentId);
      if (row) return page;
      return current;
    });
    router.replace(`/college-admin/organization/department-head-assignment?departmentId=${departmentId}`, {
      scroll: false,
    });
  };

  const handleSubmit = () => {
    if (!selectedDepartmentId || !form || !formInteractive) return;
    submit.mutate(
      { department_id: selectedDepartmentId, form },
      {
        onSuccess: (result) => {
          toast.success(result.message);
          setFormDraft({ ...result.page.form });
        },
        onError: onCollegeAdminMutationError,
      },
    );
  };

  const headers = data?.table_headers ?? ["Department", "Head of department", "Since", "Term ends", "Status"];

  return (
    <div className="space-y-5" data-figma-frame="69:133798">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Department Head Assignment"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Assign, change or rotate heads of department"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <CollegeAdminOutlineLink href={data?.rotation_policy_href ?? "/college-admin/institution/policies"}>
            <SlidersHorizontalIcon className="size-3.5" aria-hidden />
            {data?.rotation_policy_label ?? "Rotation policy"}
          </CollegeAdminOutlineLink>
          <CollegeAdminPrimaryButton
            onClick={() => {
              const first = data?.table_rows.find((r) => r.is_selected) ?? data?.table_rows[0];
              if (first) handleSelectDepartment(first.department_id);
            }}
            disabled={isLoading || !assignHeadEnabled}
            className={
              !assignHeadEnabled
                ? "cursor-not-allowed bg-[#dbe4f8] text-[#a5b4d4] opacity-100 hover:bg-[#dbe4f8]"
                : undefined
            }
          >
            {assignHeadEnabled ? <PlusIcon className="size-3.5" aria-hidden /> : null}
            {collegeAdminActionLabel(data?.assign_head_label ?? "Assign head")}
          </CollegeAdminPrimaryButton>
        </div>
      </div>

      <QueryState
        isLoading={isLoading}
        isError={isError}
        error={error}
        onRetry={() => void refetch()}
        isEmpty={false}
      >
        {data && form ? (
          <div className={cn("grid gap-5 xl:grid-cols-[minmax(0,1fr)_22rem]", isFetching && "opacity-95")}>
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.current_heads_section_title}</h3>
                <span className="text-[12px] text-[#6b7280]">{data.departments_count_label}</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full min-w-[36rem] text-left text-[13px]">
                  <thead>
                    <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                      {headers.map((header, index) => (
                        <th
                          key={header}
                          className={cn(
                            "pb-3 pt-3 font-medium",
                            index === 0 ? "px-5" : "pr-3",
                            index === headers.length - 1 ? "pr-5" : "",
                          )}
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  {!data.setup_empty_state ? (
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.table_rows.map((row) => (
                        <tr
                          key={row.department_id}
                          className={cn(
                            assignHeadEnabled && "cursor-pointer hover:bg-[#f9fafb]",
                            row.is_selected && "bg-[#f8fafc]",
                          )}
                          onClick={() => handleSelectDepartment(row.department_id)}
                        >
                          <td className="px-5 py-3 font-semibold text-[#111827]">{row.department_label}</td>
                          <td className="py-3 pr-3 text-[#374151]">{row.head_name}</td>
                          <td className="py-3 pr-3 text-[#374151]">{row.since_label}</td>
                          <td className="py-3 pr-3 text-[#374151]">{row.term_ends_label}</td>
                          <td className="py-3 pr-5">
                            <StatusPill label={row.status_label} tone={row.status_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  ) : null}
                </table>
              </div>
              {data.setup_empty_state ? (
                <OrganizationSetupEmptyState state={data.setup_empty_state} embedded />
              ) : null}

              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                <span>{data.departments_count_label}</span>
                {data.pagination.total_pages > 0 ? (
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
                      disabled={!data.pagination.has_previous}
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                    >
                      ‹
                    </button>
                    {data.pagination.page_numbers.map((num, index) =>
                      num === -1 ? (
                        <span key={`ellipsis-${index}`} className="px-1">
                          …
                        </span>
                      ) : (
                        <button
                          key={num}
                          type="button"
                          className={cn(
                            "min-w-8 rounded border px-2 py-1 tabular-nums",
                            num === data.pagination.page
                              ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]"
                              : "border-[#dce3ec]",
                          )}
                          onClick={() => setPage(num)}
                        >
                          {num}
                        </button>
                      ),
                    )}
                    <button
                      type="button"
                      className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
                      disabled={!data.pagination.has_next}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      ›
                    </button>
                  </div>
                ) : null}
              </div>
            </section>

            <aside className="space-y-4">
              <section
                className={cn(
                  "rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]",
                  !formInteractive && "opacity-90",
                )}
              >
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.assign_panel_title}</h3>
                <p className="mt-1 text-[12px] text-[#6b7280]">{data.assign_panel_subtitle}</p>
                <div className="mt-4 space-y-3">
                  <FieldSelect
                    fieldKey="faculty_user_id"
                    label={data.faculty_field_label}
                    required
                    value={form.faculty_user_id}
                    options={data.faculty_options}
                    disabled={!formInteractive}
                    onChange={(value) => updateForm({ faculty_user_id: value })}
                  />
                  <FieldSelect
                    fieldKey="appointment_type"
                    label={data.appointment_type_field_label}
                    required
                    value={form.appointment_type}
                    options={data.appointment_type_options}
                    disabled={!formInteractive}
                    onChange={(value) => updateForm({ appointment_type: value })}
                  />
                  <FieldDate
                    fieldKey="effective_from"
                    label={data.effective_from_field_label}
                    required
                    value={isoToDateInput(form.effective_from)}
                    disabled={!formInteractive}
                    onChange={(value) => updateForm({ effective_from: value })}
                  />
                  <FieldDate
                    fieldKey="term_end"
                    label={data.term_end_field_label}
                    required
                    value={isoToDateInput(form.term_end)}
                    disabled={!formInteractive}
                    onChange={(value) => updateForm({ term_end: value })}
                  />
                  <div className="space-y-1" data-field-key="order_reference">
                    <Label className="text-[12px] text-[#374151]">
                      {data.order_reference_field_label} <span className="text-[#dc2626]">*</span>
                    </Label>
                    <Input
                      value={form.order_reference}
                      disabled={!formInteractive}
                      onChange={(e) => updateForm({ order_reference: e.target.value })}
                      className="h-9 border-[#dce3ec] text-[13px] disabled:cursor-not-allowed disabled:bg-[#f9fafb]"
                    />
                  </div>
                </div>
              </section>

              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.eligibility_section_title}</h3>
                <ul className="mt-3 space-y-3">
                  {data.eligibility_rows.map((row) => (
                    <li key={row.key} className="flex items-start justify-between gap-3 text-[13px]">
                      <div className="min-w-0">
                        <p className="font-medium text-[#111827]">{row.label}</p>
                        <p className="text-[12px] text-[#6b7280]">{row.detail}</p>
                      </div>
                      <div className="flex shrink-0 items-center gap-2">
                        {row.status_tone === "success" ? (
                          <CircleCheckIcon className="size-4 text-[#10b981]" aria-hidden />
                        ) : row.status_tone === "warning" ? (
                          <TriangleAlertIcon className="size-4 text-[#f97316]" aria-hidden />
                        ) : null}
                        <EligibilityBadge label={row.status_label} tone={row.status_tone} />
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            </aside>
          </div>
        ) : null}
      </QueryState>

      {data ? (
        <footer className="flex flex-col gap-3 border-t border-[#e8ecf2] pt-4 lg:flex-row lg:items-center lg:justify-between">
          <p className="text-[12px] text-[#6b7280]">{data.footer_note}</p>
          <div className="flex flex-wrap items-center gap-2">
            <CollegeAdminOutlineButton
              onClick={() => router.push("/college-admin/organization/department-management-dashboard")}
            >
              {data.cancel_label}
            </CollegeAdminOutlineButton>
            <CollegeAdminPrimaryButton
              disabled={!data.can_submit || !form?.faculty_user_id || !selectedDepartmentId || submit.isPending || isFetching}
              onClick={handleSubmit}
            >
              {data.submit_label}
            </CollegeAdminPrimaryButton>
          </div>
        </footer>
      ) : null}
    </div>
  );
}

function FieldSelect({
  fieldKey,
  label,
  required,
  value,
  options,
  disabled,
  onChange,
}: {
  fieldKey: string;
  label: string;
  required?: boolean;
  value: string;
  options: { value: string; label: string }[];
  disabled?: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-1" data-field-key={fieldKey}>
      <Label className="text-[12px] text-[#374151]">
        {label} {required ? <span className="text-[#dc2626]">*</span> : null}
      </Label>
      <select
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className="h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151] disabled:cursor-not-allowed disabled:bg-[#f9fafb]"
      >
        {options.map((opt) => (
          <option key={`${opt.value}-${opt.label}`} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function FieldDate({
  fieldKey,
  label,
  required,
  value,
  disabled,
  onChange,
}: {
  fieldKey: string;
  label: string;
  required?: boolean;
  value: string;
  disabled?: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-1" data-field-key={fieldKey}>
      <Label className="text-[12px] text-[#374151]">
        {label} {required ? <span className="text-[#dc2626]">*</span> : null}
      </Label>
      <Input
        type="date"
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className="h-9 border-[#dce3ec] text-[13px] disabled:cursor-not-allowed disabled:bg-[#f9fafb]"
      />
    </div>
  );
}