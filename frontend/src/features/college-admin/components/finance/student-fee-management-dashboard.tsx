"use client";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  CollegeAdminOutlineButton,
  CollegeAdminPrimaryButton,
} from "@/features/college-admin/components/ui/college-admin-page-buttons";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import {
  StudentFeeAssignModal,
  type StudentFeeAssignTab,
} from "@/features/college-admin/components/finance/student-fee-assign-modal";
import {
  CollegeAdminPanelEmptyState,
  CollegeAdminTablePanel,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useStudentFeeManagementPage } from "@/features/college-admin/hooks/use-student-fee-management";
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
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium",
        styles[key],
      )}
    >
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}

function Pagination({
  data,
  page,
  setPage,
}: {
  data: NonNullable<ReturnType<typeof useStudentFeeManagementPage>["data"]>;
  page: number;
  setPage: (n: number) => void;
}) {
  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
        disabled={!data.pagination.has_previous}
        onClick={() => setPage(Math.max(1, page - 1))}
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
              "min-w-8 rounded border px-2 py-1 tabular-nums text-xs font-semibold",
              num === data.pagination.page ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]" : "border-[#dce3ec]",
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
        onClick={() => setPage(page + 1)}
      >
        ›
      </button>
    </div>
  );
}

function AssignFeeActions({
  assignStudentLabel,
  assignGroupLabel,
  bulkLabel,
  onOpen,
  centered,
}: {
  assignStudentLabel: string;
  assignGroupLabel: string;
  bulkLabel: string;
  onOpen: (tab: StudentFeeAssignTab) => void;
  centered?: boolean;
}) {
  return (
    <div className={cn("flex flex-wrap gap-2", centered ? "justify-center" : "justify-end")}>
      <CollegeAdminOutlineButton type="button" onClick={() => onOpen("single")}>
        {assignStudentLabel}
      </CollegeAdminOutlineButton>
      <CollegeAdminOutlineButton type="button" onClick={() => onOpen("group")}>
        {assignGroupLabel}
      </CollegeAdminOutlineButton>
      <CollegeAdminPrimaryButton type="button" onClick={() => onOpen("bulk")}>
        <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={bulkLabel} />
      </CollegeAdminPrimaryButton>
    </div>
  );
}

export function StudentFeeManagementDashboard() {
  const [page, setPage] = useState(1);
  const [assignOpen, setAssignOpen] = useState(false);
  const [assignTab, setAssignTab] = useState<StudentFeeAssignTab>("single");
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const { data, isLoading, isError, error, refetch } = useStudentFeeManagementPage({ page });

  const headers = data?.table_headers ?? [];
  const showHeaderActions = !data || data.student_fees.length > 0;

  const openAssign = useCallback((tab: StudentFeeAssignTab) => {
    setAssignTab(tab);
    setAssignOpen(true);
  }, []);

  useEffect(() => {
    if (searchParams.get("bulk") !== "1" || assignOpen) return;
    openAssign("bulk");
    const params = new URLSearchParams(searchParams.toString());
    params.delete("bulk");
    const qs = params.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  }, [assignOpen, openAssign, pathname, router, searchParams]);

  const labels = {
    assignStudent: data?.assign_student_label ?? "Assign student",
    assignGroup: data?.assign_group_label ?? "Assign group",
    bulk: data?.bulk_assign_label ?? "Bulk import",
  };

  return (
    <div className="space-y-5" data-figma-frame="160:2938">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Student Fee Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Assign fees to students after assessment"}
          </p>
        </div>
        {showHeaderActions ? (
          <AssignFeeActions
            assignStudentLabel={labels.assignStudent}
            assignGroupLabel={labels.assignGroup}
            bulkLabel={labels.bulk}
            onOpen={openAssign}
          />
        ) : null}
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <CollegeAdminKpiGrid>
              {data.kpis.map((kpi, index) => (
                <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
              ))}
            </CollegeAdminKpiGrid>

            <CollegeAdminTablePanel
              title={data.student_fees_section_title}
              description={data.student_fees_count_label}
              footer={
                <>
                  <span>{data.showing_label}</span>
                  {data.pagination.total_pages > 0 ? (
                    <Pagination data={data} page={page} setPage={setPage} />
                  ) : null}
                </>
              }
            >
              {data.student_fees.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[48rem] text-left text-[13px]">
                    <thead>
                      <tr className="border-b border-[#f1f5f9] text-[11px] font-semibold uppercase tracking-wide text-[#94a3b8]">
                        {headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "pb-3 pt-4 font-medium",
                              index === 0 ? "px-5" : "pr-3",
                              index === headers.length - 1 ? "pr-5 text-right" : "",
                              header === "Assessed" || header === "Concession" ? "text-right" : "",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.student_fees.map((row) => (
                        <tr key={row.assessment_id} className="transition-colors hover:bg-[#f8fafc]">
                          <td className="px-5 py-3.5 font-medium text-[#111827]">
                            <Link href={row.detail_href} className="hover:text-[#245dd8]">
                              {row.student_name}
                            </Link>
                          </td>
                          <td className="py-3.5 pr-3 font-mono text-[12px] text-[#374151]">{row.register_number}</td>
                          <td className="py-3.5 pr-3 text-[#374151]">{row.programme_label}</td>
                          <td className="py-3.5 pr-3 text-right tabular-nums font-medium text-[#111827]">
                            {row.assessed_label}
                          </td>
                          <td className="py-3.5 pr-3 text-right tabular-nums text-[#374151]">
                            {row.concession_label}
                          </td>
                          <td className="py-3.5 pr-5 text-right">
                            <StatusPill label={row.status_label} tone={row.status_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <CollegeAdminPanelEmptyState
                  iconSlug="users"
                  title="No student fee assessments yet"
                  description="Assign a published fee structure to one student, a programme group (e.g. semester cohort), or import rows from CSV/Excel."
                  action={
                    <AssignFeeActions
                      assignStudentLabel={labels.assignStudent}
                      assignGroupLabel={labels.assignGroup}
                      bulkLabel={labels.bulk}
                      onOpen={openAssign}
                      centered
                    />
                  }
                />
              )}
            </CollegeAdminTablePanel>
          </>
        ) : null}
      </QueryState>

      <StudentFeeAssignModal
        open={assignOpen}
        initialTab={assignTab}
        onClose={() => setAssignOpen(false)}
      />
    </div>
  );
}