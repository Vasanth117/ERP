"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { RefreshCwIcon } from "@/components/icons/erp/generated/refresh-cw";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAutoSuggestFacultySubjectAllocation,
  useConfirmFacultySubjectAllocation,
  useFacultySubjectAllocationPage,
} from "@/features/college-admin/hooks/use-faculty-subject-allocation";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
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

function WorkflowStepper({
  steps,
}: {
  steps: { key: string; label: string; step_number: number; status: string; href?: string | null }[];
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white px-4 py-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:px-6">
      <div className="flex flex-wrap items-center gap-y-3 sm:flex-nowrap">
        {steps.map((wizardStep, index) => {
          const active = wizardStep.status === "active";
          const done = wizardStep.status === "done";
          const inner = (
            <>
              <span
                className={cn(
                  "flex size-8 shrink-0 items-center justify-center rounded-full text-[13px] font-semibold tabular-nums",
                  active && "border-2 border-[#245dd8] bg-white text-[#245dd8]",
                  !active && !done && "border border-[#e5e7eb] bg-[#f9fafb] text-[#9ca3af]",
                  done && "border-2 border-[#245dd8] bg-[#245dd8] text-white",
                )}
              >
                {done ? <CheckIcon className="size-3.5" strokeWidth={2.5} aria-hidden /> : wizardStep.step_number}
              </span>
              <span
                className={cn(
                  "ml-2 hidden truncate text-left text-[12px] sm:inline sm:text-[13px]",
                  active ? "font-semibold text-[#111827]" : "font-medium text-[#9ca3af]",
                )}
              >
                {wizardStep.label}
              </span>
            </>
          );
          return (
            <div key={wizardStep.key} className="flex min-w-0 flex-1 items-center last:flex-none">
              {wizardStep.href && !active ? (
                <Link href={wizardStep.href} className="flex min-w-0 items-center hover:opacity-90">
                  {inner}
                </Link>
              ) : (
                <div className="flex min-w-0 items-center">{inner}</div>
              )}
              {index < steps.length - 1 ? (
                <div className="mx-2 hidden h-px min-w-[1rem] flex-1 bg-[#e5e7eb] sm:block" aria-hidden />
              ) : null}
            </div>
          );
        })}
      </div>
    </section>
  );
}

function CapacityBar({ assigned, capacity, tone }: { assigned: number; capacity: number; tone: string }) {
  const pct = capacity > 0 ? Math.min(100, Math.round((assigned / capacity) * 100)) : 0;
  const barColor =
    tone === "warning" ? "bg-[#d97706]" : tone === "info" ? "bg-[#3b82f6]" : "bg-[#10b981]";
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-[#f3f4f6]">
      <div className={cn("h-full rounded-full transition-all", barColor)} style={{ width: `${pct}%` }} />
    </div>
  );
}


export function FacultySubjectAllocationDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const query = useMemo(
    () => ({
      academic_year_label: searchParams.get("academic_year_label") ?? undefined,
      semester_label: searchParams.get("semester_label") ?? undefined,
      department_id: searchParams.get("department_id") ?? undefined,
    }),
    [searchParams],
  );

  const pageQuery = useFacultySubjectAllocationPage(query);
  const autoSuggest = useAutoSuggestFacultySubjectAllocation();
  const confirmAlloc = useConfirmFacultySubjectAllocation();

  const data = pageQuery.data;
  const [year, setYear] = useState("");
  const [semester, setSemester] = useState("");
  const [departmentId, setDepartmentId] = useState("");

  const syncFilters = useCallback(
    (next: { academic_year_label?: string; semester_label?: string; department_id?: string }) => {
      const params = new URLSearchParams(searchParams.toString());
      const ay = next.academic_year_label ?? year;
      const sem = next.semester_label ?? semester;
      const dept = next.department_id ?? departmentId;
      if (ay) params.set("academic_year_label", ay);
      else params.delete("academic_year_label");
      if (sem) params.set("semester_label", sem);
      else params.delete("semester_label");
      if (dept) params.set("department_id", dept);
      else params.delete("department_id");
      router.replace(`/college-admin/faculty/faculty-subject-allocation?${params.toString()}`);
    },
    [departmentId, router, searchParams, semester, year],
  );

  useEffect(() => {
    if (!data) return;
    setYear(data.selected_academic_year);
    setSemester(data.selected_semester_label);
    setDepartmentId(data.selected_department_id);
  }, [data]);

  const onAutoSuggest = () => {
    if (!data) return;
    autoSuggest.mutate(
      {
        academic_year_label: data.selected_academic_year,
        semester_label: data.selected_semester_label,
        department_id: data.selected_department_id,
      },
      {
        onSuccess: () => toast.success("Suggestions applied"),
        onError: onCollegeAdminMutationError,
      },
    );
  };

  const onConfirm = () => {
    if (!data) return;
    const allocations = data.subject_rows
      .filter((row) => row.faculty_record_id && row.faculty_label !== "—")
      .map((row) => ({
        course_id: row.course_id,
        faculty_record_id: row.faculty_record_id as string,
      }));
    if (!allocations.length) {
      toast.error("No allocations to confirm. Run auto-suggest or assign subjects first.");
      return;
    }
    confirmAlloc.mutate(
      {
        academic_year_label: data.selected_academic_year,
        semester_label: data.selected_semester_label,
        department_id: data.selected_department_id,
        allocations,
      },
      {
        onSuccess: () => toast.success("Allocation confirmed"),
        onError: onCollegeAdminMutationError,
      },
    );
  };

  const isBusy = autoSuggest.isPending || confirmAlloc.isPending;

  return (
    <div className="space-y-5" data-figma-frame="159:4759">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Faculty Subject Allocation"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Allocate subjects for the active semester"}
          </p>
          {data ? (
            <div className="mt-3 flex flex-wrap items-center gap-2 text-[12px] text-[#6b7280]">
              <select
                aria-label={data.semester_filter_label}
                className="h-8 rounded-md border border-[#dce3ec] bg-white px-2 text-[12px]"
                value={data.selected_semester_label}
                onChange={(e) => syncFilters({ semester_label: e.target.value })}
              >
                {data.semester_options.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <select
                aria-label={data.department_filter_label}
                className="h-8 rounded-md border border-[#dce3ec] bg-white px-2 text-[12px]"
                value={data.selected_department_id}
                onChange={(e) => syncFilters({ department_id: e.target.value })}
              >
                {data.department_options.filter((o) => o.value).map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          ) : null}
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            disabled={!data || isBusy}
            onClick={onAutoSuggest}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
          >
            <RefreshCwIcon className="size-3.5" aria-hidden />
            {data?.auto_suggest_label ?? "Auto-suggest"}
          </button>
          <button
            type="button"
            disabled={!data || isBusy}
            onClick={onConfirm}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
          >
            <CheckIcon className="size-3.5" aria-hidden />
            {data?.confirm_label ?? "Confirm allocation"}
          </button>
        </div>
      </div>

      {data ? <WorkflowStepper steps={data.workflow_steps} /> : null}

      <QueryState
        isLoading={pageQuery.isLoading}
        isError={pageQuery.isError}
        error={pageQuery.error}
        onRetry={() => void pageQuery.refetch()}
      >
        {data ? (
          <>
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_300px]">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.subjects_section_title}</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[640px] text-left text-[13px]">
                    <thead className="border-b border-[#f1f5f9] bg-[#f9fafb] text-[11px] font-semibold uppercase tracking-wide text-[#6b7280]">
                      <tr>
                        {data.table_headers.map((h) => (
                          <th key={h} className="px-4 py-2.5 font-semibold">
                            {h}
                          </th>
                        ))}
                        <th className="px-4 py-2.5" />
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.subject_rows.map((row) => (
                        <tr key={row.course_id} className="hover:bg-[#fafbfc]">
                          <td className="px-4 py-3 font-medium text-[#111827]">{row.subject_name}</td>
                          <td className="px-4 py-3 font-mono text-[#6b7280]">{row.subject_code}</td>
                          <td className="px-4 py-3 tabular-nums text-[#374151]">{row.semester_label}</td>
                          <td className="px-4 py-3 tabular-nums text-[#374151]">{row.hours_label}</td>
                          <td className="px-4 py-3 text-[#374151]">{row.faculty_label}</td>
                          <td className="px-4 py-3 text-right">
                            {row.status_label ? (
                              <StatusPill label={row.status_label} tone={row.status_tone ?? "muted"} />
                            ) : null}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">{data.subjects_footer_label}</p>
              </section>

              <Section title={data.capacity_section_title}>
                <ul className="space-y-5">
                  {data.capacity_rows.map((row) => (
                    <li key={row.faculty_record_id}>
                      <div className="flex items-baseline justify-between gap-2">
                        <p className="text-[13px] font-medium text-[#111827]">{row.faculty_name}</p>
                        <p className="text-[11px] tabular-nums text-[#6b7280]">{row.hours_assigned_label}</p>
                      </div>
                      <div className="mt-2">
                        <CapacityBar
                          assigned={row.assigned_hours}
                          capacity={row.capacity_hours}
                          tone={row.load_tone}
                        />
                      </div>
                    </li>
                  ))}
                </ul>
              </Section>
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="border-b border-[#f1f5f9] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
      </div>
      <div className="px-5 py-4">{children}</div>
    </section>
  );
}