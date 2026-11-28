"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";

import { UploadIcon } from "@/components/icons/erp/generated/upload";
import { XIcon } from "@/components/icons/erp/generated/x";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  CollegeAdminPrimaryButton,
  CollegeAdminSecondaryButton,
} from "@/features/college-admin/components/ui/college-admin-action-button";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAssignStudentFee,
  useAssignStudentFeeBulk,
  useAssignStudentFeeGroup,
  useStudentFeeAssignPage,
} from "@/features/college-admin/hooks/use-student-fee-assign";
import type { FeeAssessmentBulkRow } from "@/features/college-admin/types/student-fee-assign";
import { cn } from "@/lib/utils";

export type StudentFeeAssignTab = "single" | "group" | "bulk";

type Props = {
  open: boolean;
  initialTab?: StudentFeeAssignTab;
  onClose: () => void;
};

function parseBulkFile(text: string): FeeAssessmentBulkRow[] {
  const lines = text
    .trim()
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (!lines.length) return [];

  const splitRow = (line: string) => line.split(/[,;\t]/).map((cell) => cell.trim());
  const first = splitRow(lines[0]).map((h) => h.toLowerCase());
  const hasHeader = first.some((cell) => cell.includes("register"));

  const dataLines = hasHeader ? lines.slice(1) : lines;
  const regIdx = hasHeader ? first.findIndex((c) => c.includes("register")) : 0;
  const structIdx = hasHeader ? first.findIndex((c) => c.includes("structure")) : 1;
  const conIdx = hasHeader ? first.findIndex((c) => c.includes("concession")) : 2;

  return dataLines
    .map((line) => {
      const cells = splitRow(line);
      const register_number = cells[regIdx >= 0 ? regIdx : 0] ?? "";
      const structure_id = structIdx >= 0 ? cells[structIdx] || undefined : cells[1];
      const concessionRaw = conIdx >= 0 ? cells[conIdx] : cells[2];
      const concession_amount = concessionRaw ? Number(concessionRaw) || 0 : 0;
      return { register_number, structure_id: structure_id || undefined, concession_amount };
    })
    .filter((row) => row.register_number);
}

export function StudentFeeAssignModal({ open, initialTab = "single", onClose }: Props) {
  const { data, isLoading, isError, error, refetch } = useStudentFeeAssignPage(open);
  const assignSingle = useAssignStudentFee();
  const assignGroup = useAssignStudentFeeGroup();
  const assignBulk = useAssignStudentFeeBulk();

  const [tab, setTab] = useState<StudentFeeAssignTab>(initialTab);
  const [structureId, setStructureId] = useState("");
  const [studentUserId, setStudentUserId] = useState("");
  const [concession, setConcession] = useState("0");
  const [programmeCode, setProgrammeCode] = useState("");
  const [batchLabel, setBatchLabel] = useState("");
  const [sectionCode, setSectionCode] = useState("");
  const [bulkDefaultStructure, setBulkDefaultStructure] = useState("");
  const [bulkRows, setBulkRows] = useState<FeeAssessmentBulkRow[]>([]);
  const [formError, setFormError] = useState<string | null>(null);
  const [resultSummary, setResultSummary] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setTab(initialTab);
      setFormError(null);
      setResultSummary(null);
    }
  }, [initialTab, open]);

  const selectedStructure = useMemo(
    () => data?.structure_options.find((s) => s.structure_id === structureId),
    [data?.structure_options, structureId],
  );

  const groupPreviewCount = useMemo(() => {
    if (!data || !programmeCode) return 0;
    return data.student_options.filter((s) => {
      if (s.programme_code !== programmeCode) return false;
      if (batchLabel && (s.batch_label || "") !== batchLabel) return false;
      if (sectionCode && (s.section_code || "") !== sectionCode) return false;
      return true;
    }).length;
  }, [batchLabel, data, programmeCode, sectionCode]);

  const busy = assignSingle.isPending || assignGroup.isPending || assignBulk.isPending;

  const onKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === "Escape" && !busy) onClose();
    },
    [busy, onClose],
  );

  useEffect(() => {
    if (!open) return;
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onKeyDown, open]);

  const handleFile = useCallback((file: File | null) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const text = typeof reader.result === "string" ? reader.result : "";
      setBulkRows(parseBulkFile(text));
    };
    reader.readAsText(file);
  }, []);

  const submit = useCallback(async () => {
    setFormError(null);
    setResultSummary(null);
    try {
      if (tab === "single") {
        if (!studentUserId || !structureId || !selectedStructure) {
          setFormError("Select a student and fee structure.");
          return;
        }
        await assignSingle.mutateAsync({
          student_user_id: studentUserId,
          structure_id: structureId,
          academic_year_label: selectedStructure.academic_year_label,
          semester_label: selectedStructure.semester_label,
          concession_amount: Number(concession) || 0,
        });
        setResultSummary("Fee structure assigned to the student.");
        onClose();
        return;
      }
      if (tab === "group") {
        if (!structureId || !programmeCode) {
          setFormError("Select a fee structure and programme.");
          return;
        }
        const result = await assignGroup.mutateAsync({
          structure_id: structureId,
          programme_code: programmeCode,
          batch_label: batchLabel || null,
          section_code: sectionCode || null,
        });
        setResultSummary(
          `Assigned ${result.succeeded} student(s)${result.skipped ? `, skipped ${result.skipped} already assigned` : ""}.`,
        );
        if (!result.failed.length) onClose();
        return;
      }
      if (!bulkRows.length) {
        setFormError("Upload a CSV or Excel-exported file with at least one student row.");
        return;
      }
      const result = await assignBulk.mutateAsync({
        default_structure_id: bulkDefaultStructure || null,
        rows: bulkRows,
      });
      setResultSummary(
        `Processed ${result.processed ?? bulkRows.length}: ${result.succeeded} assigned, ${result.skipped} skipped, ${result.failed.length} failed.`,
      );
      if (!result.failed.length) onClose();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Assignment failed");
    }
  }, [
    assignBulk,
    assignGroup,
    assignSingle,
    batchLabel,
    bulkDefaultStructure,
    bulkRows,
    concession,
    onClose,
    programmeCode,
    sectionCode,
    selectedStructure,
    structureId,
    studentUserId,
    tab,
  ]);

  if (!open || typeof document === "undefined") return null;

  const shell = (
    <div className="fixed inset-0 z-[85] flex items-center justify-center bg-[#0f172a]/45 p-4 sm:p-6">
      <button type="button" className="absolute inset-0 cursor-default" aria-label="Close" onClick={onClose} />
      <div
        role="dialog"
        aria-modal="true"
        className="relative flex max-h-[min(90vh,880px)] w-full max-w-[min(640px,calc(100vw-2rem))] flex-col overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-2xl"
      >
        <header className="flex items-center justify-between border-b border-[#e8ecf2] px-5 py-3.5">
          <div>
            <p className="text-[15px] font-semibold text-[#111827]">{data?.page_title ?? "Assign fees"}</p>
            <p className="text-[12px] text-[#6b7280]">{data?.page_subtitle}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex size-8 items-center justify-center rounded-md text-[#6b7280] hover:bg-[#f3f4f6]"
          >
            <XIcon className="size-4" aria-hidden />
          </button>
        </header>

        <div className="flex gap-1 border-b border-[#e8ecf2] bg-[#fafbfc] px-4 py-2">
          {(
            [
              ["single", data?.single_tab_label ?? "Single student"],
              ["group", data?.group_tab_label ?? "Group"],
              ["bulk", data?.bulk_tab_label ?? "Bulk import"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setTab(key)}
              className={cn(
                "rounded-lg px-3 py-1.5 text-[12px] font-semibold transition-colors",
                tab === key ? "bg-white text-[#245dd8] shadow-sm" : "text-[#6b7280] hover:text-[#374151]",
              )}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
          <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
            {data ? (
              <div className="space-y-4">
                {tab !== "bulk" ? (
                  <label className="block text-[13px] text-[#374151]">
                    <span className="mb-1 block font-medium">{data.structure_label}</span>
                    <select
                      value={structureId}
                      onChange={(e) => setStructureId(e.target.value)}
                      className="h-10 w-full rounded-lg border border-[#dce3ec] px-3 text-[13px]"
                    >
                      <option value="">Select fee structure</option>
                      {data.structure_options.map((opt) => (
                        <option key={opt.structure_id} value={opt.structure_id}>
                          {opt.label} ({opt.total_label})
                        </option>
                      ))}
                    </select>
                  </label>
                ) : null}

                {tab === "single" ? (
                  <>
                    <label className="block text-[13px] text-[#374151]">
                      <span className="mb-1 block font-medium">{data.student_label}</span>
                      <select
                        value={studentUserId}
                        onChange={(e) => setStudentUserId(e.target.value)}
                        className="h-10 w-full rounded-lg border border-[#dce3ec] px-3 text-[13px]"
                      >
                        <option value="">Select student</option>
                        {data.student_options.map((opt) => (
                          <option key={opt.student_user_id} value={opt.student_user_id}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="block text-[13px] text-[#374151]">
                      <span className="mb-1 block font-medium">{data.concession_label}</span>
                      <Input
                        type="number"
                        min={0}
                        value={concession}
                        onChange={(e) => setConcession(e.target.value)}
                        className="h-10 border-[#dce3ec]"
                      />
                    </label>
                  </>
                ) : null}

                {tab === "group" ? (
                  <>
                    <label className="block text-[13px] text-[#374151]">
                      <span className="mb-1 block font-medium">{data.programme_label}</span>
                      <select
                        value={programmeCode}
                        onChange={(e) => setProgrammeCode(e.target.value)}
                        className="h-10 w-full rounded-lg border border-[#dce3ec] px-3 text-[13px]"
                      >
                        {data.programme_options.map((opt) => (
                          <option key={`${opt.value}-${opt.label}`} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <label className="block text-[13px] text-[#374151]">
                        <span className="mb-1 block font-medium">{data.batch_filter_label}</span>
                        <select
                          value={batchLabel}
                          onChange={(e) => setBatchLabel(e.target.value)}
                          className="h-10 w-full rounded-lg border border-[#dce3ec] px-3 text-[13px]"
                        >
                          {data.batch_options.map((opt) => (
                            <option key={`batch-${opt.value}`} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label className="block text-[13px] text-[#374151]">
                        <span className="mb-1 block font-medium">{data.section_filter_label}</span>
                        <select
                          value={sectionCode}
                          onChange={(e) => setSectionCode(e.target.value)}
                          className="h-10 w-full rounded-lg border border-[#dce3ec] px-3 text-[13px]"
                        >
                          {data.section_options.map((opt) => (
                            <option key={`section-${opt.value}`} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </label>
                    </div>
                    <p className="rounded-lg border border-dashed border-[#dce3ec] bg-[#fafbfc] px-3 py-2 text-[12px] text-[#64748b]">
                      {programmeCode
                        ? `${groupPreviewCount} enrolled student(s) match this group for the selected structure term.`
                        : "Choose a programme to preview how many students will be assigned."}
                    </p>
                  </>
                ) : null}

                {tab === "bulk" ? (
                  <>
                    <label className="block text-[13px] text-[#374151]">
                      <span className="mb-1 block font-medium">Default fee structure (optional)</span>
                      <select
                        value={bulkDefaultStructure}
                        onChange={(e) => setBulkDefaultStructure(e.target.value)}
                        className="h-10 w-full rounded-lg border border-[#dce3ec] px-3 text-[13px]"
                      >
                        <option value="">Use structure_id from each row</option>
                        {data.structure_options.map((opt) => (
                          <option key={opt.structure_id} value={opt.structure_id}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <div>
                      <Label className="text-[13px] font-medium text-[#374151]">{data.bulk_file_label}</Label>
                      <label className="mt-1.5 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-[#c7dafc] bg-[#f8fbff] px-4 py-6 text-center hover:bg-[#eff6ff]">
                        <UploadIcon className="size-6 text-[#245dd8]" aria-hidden />
                        <span className="text-[12px] font-medium text-[#1d4ed8]">Choose CSV or Excel-exported file</span>
                        <span className="text-[11px] text-[#64748b]">{data.bulk_template_hint}</span>
                        <input
                          type="file"
                          accept=".csv,.txt,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                          className="sr-only"
                          onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
                        />
                      </label>
                      {bulkRows.length ? (
                        <p className="mt-2 text-[12px] text-[#047857]">{bulkRows.length} row(s) ready to import.</p>
                      ) : null}
                    </div>
                  </>
                ) : null}

                {formError ? <p className="text-[13px] text-[#b91c1c]">{formError}</p> : null}
                {resultSummary ? <p className="text-[13px] text-[#047857]">{resultSummary}</p> : null}
              </div>
            ) : null}
          </QueryState>
        </div>

        <footer className="flex justify-end gap-2 border-t border-[#e8ecf2] px-5 py-3">
          <CollegeAdminSecondaryButton disabled={busy} onClick={onClose}>
            Cancel
          </CollegeAdminSecondaryButton>
          <CollegeAdminPrimaryButton disabled={busy || isLoading} onClick={() => void submit()}>
            {data?.assign_submit_label ?? "Assign fees"}
          </CollegeAdminPrimaryButton>
        </footer>
      </div>
    </div>
  );

  return createPortal(shell, document.body);
}