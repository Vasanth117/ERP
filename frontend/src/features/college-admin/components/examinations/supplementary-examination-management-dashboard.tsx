"use client";

import { useState } from "react";
import { toast } from "sonner";

import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { Button } from "@/components/ui/button";
import { ExaminationRegistrationSubNav } from "@/features/college-admin/components/examinations/examination-registration-sub-nav";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useCreateSupplementaryExaminationSession,
  useSupplementaryExaminationManagementPage,
} from "@/features/college-admin/hooks/use-supplementary-examination-management";
import type { SupplementaryExaminationManagementPage } from "@/features/college-admin/types/supplementary-examination-management";
import { cn } from "@/lib/utils";


function Pagination({
  data,
  page,
  setPage,
}: {
  data: SupplementaryExaminationManagementPage;
  page: number;
  setPage: (p: number) => void;
}) {
  return (
    <div className="flex items-center gap-1">
      <button type="button" className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40" disabled={!data.pagination.has_previous} onClick={() => setPage(Math.max(1, page - 1))}>
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
            className={cn("min-w-8 rounded border px-2 py-1 tabular-nums", num === data.pagination.page ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]" : "border-[#dce3ec]")}
            onClick={() => setPage(num)}
          >
            {num}
          </button>
        ),
      )}
      <button type="button" className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40" disabled={!data.pagination.has_next} onClick={() => setPage(page + 1)}>
        ›
      </button>
    </div>
  );
}

export function SupplementaryExaminationManagementDashboard() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useSupplementaryExaminationManagementPage({ page });
  const createSession = useCreateSupplementaryExaminationSession();

  const handleCreate = () => {
    createSession.mutate(
      { page, session_id: data?.selected_session_id || undefined },
      {
        onSuccess: () => toast.success("Supplementary session created."),
        onError: (e: Error) => toast.error(e.message),
      },
    );
  };

  return (
    <div className="space-y-5" data-figma-frame="CA-09-supplementary">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{data?.page_title ?? "Supplementary Examination Management"}</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "Supplementary and arrear examinations"}</p>
        </div>
        <Button
          type="button"
          className="h-9 shrink-0 gap-1.5 bg-[#245dd8] text-xs font-medium hover:bg-[#1f4fb8]"
          disabled={createSession.isPending}
          onClick={handleCreate}
        >
          <PlusIcon className="size-3.5" aria-hidden />
          {data?.create_session_label ?? "Create session"}
        </Button>
      </div>

      {data?.sub_nav?.length ? <ExaminationRegistrationSubNav items={data.sub_nav} /> : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <CollegeAdminKpiGrid>
              {data.kpis.map((kpi, index) => (
                <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
              ))}
            </CollegeAdminKpiGrid>

            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.arrear_subjects_section_title}</h3>
              </div>
              {data.arrear_subject_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[44rem] text-left text-[13px]">
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
                      {data.arrear_subject_rows.map((row) => (
                        <tr key={row.course_code}>
                          <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">{row.subject_label}</td>
                          <td className="py-3 pr-3 tabular-nums text-[#6b7280]">{row.course_code}</td>
                          <td className="py-3 pr-3 tabular-nums">{row.students_count.toLocaleString("en-IN")}</td>
                          <td className="py-3 pr-3 text-[#6b7280]">{row.date_label}</td>
                          <td className="py-3 pr-5 text-[#6b7280]">{row.hall_label}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">No arrear subjects to display yet.</p>
              )}
              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                <span>{data.showing_label}</span>
                {data.pagination.total_pages > 1 ? <Pagination data={data} page={page} setPage={setPage} /> : null}
              </div>
            </section>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}