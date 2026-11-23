"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { SendHorizontalIcon } from "@/components/icons/erp/generated/send-horizontal";
import { UploadIcon } from "@/components/icons/erp/generated/upload";
import { Label } from "@/components/ui/label";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useEmployeeDocumentVerificationPage,
  useSaveEmployeeDocumentDecision,
  useVerifyAllEmployeeDocuments,
} from "@/features/college-admin/hooks/use-employee-document-verification";
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


export function EmployeeDocumentVerificationDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const documentId = useMemo(() => searchParams.get("document_id") ?? undefined, [searchParams]);

  const pageQuery = useEmployeeDocumentVerificationPage(documentId);
  const data = pageQuery.data;

  const [result, setResult] = useState("");
  const [remarks, setRemarks] = useState("");

  const activeDocId = data?.selected_document_id ?? documentId;
  const saveDecision = useSaveEmployeeDocumentDecision(activeDocId);
  const verifyAll = useVerifyAllEmployeeDocuments();

  useEffect(() => {
    if (data?.decision_result !== undefined) setResult(data.decision_result);
    if (data?.decision_remarks !== undefined) setRemarks(data.decision_remarks);
  }, [data?.decision_result, data?.decision_remarks, data?.selected_document_id]);

  const selectDocument = (id: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("document_id", id);
    router.push(`/college-admin/faculty/employee-document-verification?${params.toString()}`);
  };

  const handleSaveDecision = () => {
    if (!activeDocId || !result) {
      toast.error("Select a document and result before saving");
      return;
    }
    saveDecision.mutate(
      { document_id: activeDocId, result, remarks: remarks || undefined },
      {
        onSuccess: () => toast.success("Decision saved"),
        onError: onCollegeAdminMutationError,
      },
    );
  };

  const handleVerifyAll = () => {
    verifyAll.mutate(undefined, {
      onSuccess: () => toast.success("Pending documents marked verified"),
      onError: onCollegeAdminMutationError,
    });
  };

  const isBusy = saveDecision.isPending || verifyAll.isPending;

  return (
    <div className="space-y-5" data-figma-frame="CA-07.11">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Employee Document Verification"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Verify joining and qualification documents"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            href={data?.request_document_href ?? "/college-admin/faculty/employee-directory"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            <SendHorizontalIcon className="size-3.5" aria-hidden />
            {data?.request_document_label ?? "Request document"}
          </Link>
          <button
            type="button"
            disabled={isBusy}
            onClick={handleVerifyAll}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
          >
            <CheckIcon className="size-3.5" aria-hidden />
            {data?.verify_all_label ?? "Verify all"}
          </button>
        </div>
      </div>

      <QueryState
        isLoading={pageQuery.isLoading}
        isError={pageQuery.isError}
        error={pageQuery.error}
        onRetry={() => void pageQuery.refetch()}
      >
        {data ? (
          <>
            <CollegeAdminKpiGrid>
              {data.kpis.map((kpi, index) => (
                <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
              ))}
            </CollegeAdminKpiGrid>

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_320px]">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.documents_section_title}</h3>
                  <span className="text-[12px] text-[#6b7280]">{data.documents_footer_label}</span>
                </div>
                {data.document_rows.length ? (
                  <MotionTable>
                    <table className="w-full min-w-[40rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {data.table_headers.map((header, index) => (
                            <th key={header} className={cn("pb-3 font-medium", index === 0 ? "px-5" : "pr-3")}>
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.document_rows.map((row) => (
                          <tr
                            key={row.document_id}
                            className={cn(
                              "cursor-pointer transition-colors",
                              row.is_selected ? "bg-[#eff6ff]" : "hover:bg-[#f9fafb]",
                            )}
                            onClick={() => selectDocument(row.document_id)}
                          >
                            <td className="px-5 py-3 font-medium text-[#111827]">{row.employee_name}</td>
                            <td className="py-3 pr-3 text-[#374151]">{row.document_label}</td>
                            <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.uploaded_label}</td>
                            <td className="py-3 pr-5">
                              <StatusPill label={row.status_label} tone={row.status_tone} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </MotionTable>
                ) : (
                  <p className="px-5 py-8 text-sm text-[#9ca3af]">No employee documents awaiting verification.</p>
                )}
              </section>

              <div className="space-y-5">
                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">{data.preview_title}</h3>
                  </div>
                  <div className="px-5 py-6">
                    {data.preview_file_name ? (
                      <div className="flex flex-col items-center rounded-lg border border-dashed border-[#dce3ec] bg-[#f9fafb] px-4 py-8 text-center">
                        <UploadIcon className="size-8 text-[#9ca3af]" aria-hidden />
                        <p className="mt-3 text-[13px] font-medium text-[#111827]">{data.preview_file_name}</p>
                        {data.preview_meta_label ? (
                          <p className="mt-1 text-[12px] text-[#6b7280]">{data.preview_meta_label}</p>
                        ) : null}
                        {data.browse_files_href ? (
                          <Link
                            href={data.browse_files_href}
                            className="mt-4 inline-flex h-8 items-center rounded-md border border-[#dce3ec] bg-white px-3 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
                          >
                            {data.browse_files_label}
                          </Link>
                        ) : (
                          <button
                            type="button"
                            disabled
                            className="mt-4 inline-flex h-8 items-center rounded-md border border-[#dce3ec] bg-white px-3 text-xs font-medium text-[#6b7280]"
                          >
                            {data.browse_files_label}
                          </button>
                        )}
                      </div>
                    ) : (
                      <p className="text-sm text-[#9ca3af]">{data.preview_empty_label}</p>
                    )}
                  </div>
                </section>

                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">{data.decision_section_title}</h3>
                  </div>
                  <div className="space-y-4 px-5 py-4">
                    <div className="space-y-1.5">
                      <Label className="text-[13px] font-medium text-[#374151]">
                        {data.result_field_label} <span className="text-[#dc2626]">*</span>
                      </Label>
                      <select
                        className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                        value={result}
                        onChange={(e) => setResult(e.target.value)}
                        disabled={!activeDocId}
                      >
                        {data.result_options.map((opt) => (
                          <option key={opt.value || opt.label} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-[13px] font-medium text-[#374151]">{data.remarks_field_label}</Label>
                      <textarea
                        className="min-h-[5rem] w-full rounded-md border border-[#dce3ec] px-3 py-2 text-[13px]"
                        value={remarks}
                        onChange={(e) => setRemarks(e.target.value)}
                        disabled={!activeDocId}
                      />
                    </div>
                    <button
                      type="button"
                      disabled={isBusy || !activeDocId}
                      onClick={handleSaveDecision}
                      className="inline-flex h-9 w-full items-center justify-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
                    >
                      {data.submit_decision_label}
                    </button>
                  </div>
                </section>
              </div>
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}

function MotionTable({ children }: { children: React.ReactNode }) {
  return <div className="overflow-x-auto">{children}</div>;
}