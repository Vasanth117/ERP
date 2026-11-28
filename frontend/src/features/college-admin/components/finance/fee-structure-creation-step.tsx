"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { Trash2Icon } from "@/components/icons/erp/generated/trash-2";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  CollegeAdminPrimaryButton,
  CollegeAdminSecondaryButton,
} from "@/features/college-admin/components/ui/college-admin-action-button";
import {
  CollegeAdminPanelChromeFooter,
  CollegeAdminPanelChromeHeader,
  CollegeAdminPanelShell,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { useFinanceCreationFlow } from "@/features/college-admin/context/finance-creation-flow-context";
import {
  useFeeStructureCreationPage,
  usePublishFeeStructure,
  useSaveFeeStructure,
} from "@/features/college-admin/hooks/use-fee-structure-creation";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import { cn } from "@/lib/utils";

const STREAM_PILL_LABELS: Record<string, string> = {
  "": "All",
  undergraduate: "UG",
  postgraduate: "PG",
  doctoral: "Doctoral",
};

function streamShort(level: string) {
  if (level === "undergraduate") return "UG";
  if (level === "postgraduate") return "PG";
  if (level === "doctoral") return "DR";
  return "GEN";
}

function ScopeField({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="block">
      <Label className="text-[13px] font-medium text-[#374151]">
        {label}
        {required ? <span className="text-[#dc2626]"> *</span> : null}
      </Label>
      <div className="mt-1.5">{children}</div>
    </div>
  );
}

function ScopeSelect({
  label,
  value,
  onChange,
  options,
  required,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  required?: boolean;
  placeholder?: string;
}) {
  return (
    <ScopeField label={label} required={required}>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-10 w-full rounded-lg border border-[#dce3ec] bg-white px-3 text-[13px] text-[#111827] shadow-[0_1px_2px_rgba(15,23,42,0.04)] focus:border-[#245dd8] focus:outline-none focus:ring-2 focus:ring-[#245dd8]/20"
      >
        {placeholder ? (
          <option value="" disabled={required}>
            {placeholder}
          </option>
        ) : null}
        {options.map((opt) => (
          <option key={`${opt.value}-${opt.label}`} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </ScopeField>
  );
}

export function FeeStructureCreationStep() {
  const flow = useFinanceCreationFlow();
  const queryClient = useQueryClient();
  const { data, isLoading, isError, error, refetch } = useFeeStructureCreationPage();
  const save = useSaveFeeStructure();
  const publish = usePublishFeeStructure();

  const [departmentId, setDepartmentId] = useState("");
  const [stream, setStream] = useState("");
  const [programmeCode, setProgrammeCode] = useState("");
  const [academicYear, setAcademicYear] = useState("");
  const [semester, setSemester] = useState("");
  const [lineItems, setLineItems] = useState<{ name: string; amount: number }[]>([]);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (data?.default_line_items?.length) {
      setLineItems(data.default_line_items.map((row) => ({ ...row })));
    }
    if (data?.academic_year_options?.[0]?.value) {
      setAcademicYear((prev) => prev || data.academic_year_options[0].value);
    }
  }, [data]);

  const programmes = useMemo(() => {
    if (!data) return [];
    return data.programme_options.filter((prog) => {
      if (departmentId && prog.department_id !== departmentId) return false;
      if (stream && (prog.programme_level || "") !== stream) return false;
      return true;
    });
  }, [data, departmentId, stream]);

  useEffect(() => {
    if (!programmeCode && programmes.length === 1) {
      setProgrammeCode(programmes[0].programme_code);
    }
  }, [programmeCode, programmes]);

  const total = useMemo(
    () => lineItems.reduce((sum, row) => sum + (Number(row.amount) || 0), 0),
    [lineItems],
  );

  const selectedProg = programmes.find((p) => p.programme_code === programmeCode);

  const structureIdPreview = useMemo(() => {
    if (!programmeCode || !academicYear || !semester) return null;
    const dept =
      selectedProg?.department_name?.split(/\s+/)[0]?.slice(0, 4).toUpperCase() || "DEPT";
    const strm = streamShort(stream || selectedProg?.programme_level || "");
    const ay = academicYear.replace(/\s+/g, "");
    return `${dept}-${programmeCode}-${strm}-S${semester}-${ay}`;
  }, [academicYear, programmeCode, selectedProg, semester, stream]);

  const buildStructureId = useCallback(() => structureIdPreview ?? "NEW-STRUCTURE", [structureIdPreview]);

  const persist = useCallback(
    async (publishAfter: boolean): Promise<boolean> => {
      if (!programmeCode || !academicYear || !semester) {
        setFormError("Select programme, academic year and semester.");
        return false;
      }
      setFormError(null);
      const structureId = buildStructureId();
      const scopeMeta = {
        type: "scope",
        department_id: departmentId || selectedProg?.department_id || null,
        department_name: selectedProg?.department_name || null,
        programme_level: stream || selectedProg?.programme_level || null,
      };
      const items = [scopeMeta, ...lineItems.filter((r) => r.name.trim())];
      try {
        await save.mutateAsync({
          structure_id: structureId,
          programme_code: programmeCode,
          academic_year_label: academicYear,
          semester_label: semester,
          line_items: items,
          total_amount: total,
        });
        flow.setStructureId(structureId);
        if (publishAfter) {
          await publish.mutateAsync(structureId);
        }
        void queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.feeStructureManagementPage() });
        return true;
      } catch (err) {
        setFormError(err instanceof Error ? err.message : "Could not save fee structure");
        return false;
      }
    },
    [
      academicYear,
      buildStructureId,
      departmentId,
      flow,
      lineItems,
      programmeCode,
      publish,
      queryClient,
      save,
      selectedProg,
      semester,
      stream,
      total,
    ],
  );

  const streamOptions = data?.stream_options ?? [];

  return (
    <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
      {data ? (
        <div className="space-y-5">
          <CollegeAdminPanelShell>
            <CollegeAdminPanelChromeHeader
              title="Programme scope"
              description="Narrow by department and stream, then choose the programme and term."
            />
            <div className="space-y-5 p-5">
              <div className="grid gap-4 sm:grid-cols-2">
                <ScopeSelect
                  label={data.department_filter_label}
                  value={departmentId}
                  onChange={(v) => {
                    setDepartmentId(v);
                    setProgrammeCode("");
                  }}
                  options={data.department_options}
                />
                <ScopeSelect
                  label={data.academic_year_filter_label}
                  value={academicYear}
                  onChange={setAcademicYear}
                  options={data.academic_year_options}
                  required
                />
              </div>

              <div>
                <Label className="text-[13px] font-medium text-[#374151]">{data.stream_filter_label}</Label>
                <div className="mt-2 flex flex-wrap gap-2" role="group" aria-label={data.stream_filter_label}>
                  {streamOptions.map((opt) => {
                    const active = stream === opt.value;
                    const pill = STREAM_PILL_LABELS[opt.value] ?? opt.label;
                    return (
                      <button
                        key={opt.value || "all"}
                        type="button"
                        onClick={() => {
                          setStream(opt.value);
                          setProgrammeCode("");
                        }}
                        className={cn(
                          "h-9 rounded-lg border px-3.5 text-[12px] font-semibold transition-colors",
                          active
                            ? "border-[#245dd8] bg-[#eff6ff] text-[#1d4ed8] shadow-[0_0_0_1px_rgba(36,93,216,0.15)]"
                            : "border-[#e5e7eb] bg-white text-[#6b7280] hover:border-[#c7dafc] hover:bg-[#f8fbff]",
                        )}
                      >
                        {pill}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <ScopeSelect
                  label={data.programme_filter_label}
                  value={programmeCode}
                  onChange={setProgrammeCode}
                  options={[
                    { value: "", label: "Select programme" },
                    ...programmes.map((prog) => ({
                      value: prog.programme_code,
                      label: [prog.programme_label, prog.stream_label, prog.department_name]
                        .filter(Boolean)
                        .join(" · "),
                    })),
                  ]}
                  required
                  placeholder="Select programme"
                />
                <ScopeSelect
                  label={data.semester_filter_label}
                  value={semester}
                  onChange={setSemester}
                  options={[{ value: "", label: "Select semester" }, ...data.semester_options]}
                  required
                  placeholder="Select semester"
                />
              </div>

              {structureIdPreview ? (
                <p className="rounded-lg border border-dashed border-[#dce3ec] bg-[#fafbfc] px-3 py-2 text-[12px] text-[#64748b]">
                  Structure reference{" "}
                  <span className="font-mono font-medium text-[#111827]">{structureIdPreview}</span>
                </p>
              ) : null}
            </div>
          </CollegeAdminPanelShell>

          <CollegeAdminPanelShell>
            <CollegeAdminPanelChromeHeader
              title="Fee heads"
              description="Amounts in INR. Add or remove heads to match your college policy."
              trailing={
                <button
                  type="button"
                  onClick={() => setLineItems((prev) => [...prev, { name: "", amount: 0 }])}
                  className="inline-flex h-8 items-center gap-1 rounded-md border border-[#dce3ec] bg-white px-2.5 text-[11px] font-semibold text-[#374151] hover:bg-[#f9fafb]"
                >
                  <PlusIcon className="size-3.5" aria-hidden />
                  Add head
                </button>
              }
            />
            <div className="overflow-x-auto">
              <table className="w-full min-w-[28rem] text-left text-[13px]">
                <thead>
                  <tr className="border-b border-[#eef2f7] text-[11px] font-semibold uppercase tracking-wide text-[#94a3b8]">
                    <th className="px-5 py-3 font-medium">Fee head</th>
                    <th className="w-36 px-3 py-3 text-right font-medium">Amount (₹)</th>
                    <th className="w-12 px-3 py-3" aria-label="Remove" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f1f5f9]">
                  {lineItems.map((row, index) => (
                    <tr key={`${row.name}-${index}`} className="hover:bg-[#fafbfc]/80">
                      <td className="px-5 py-2.5">
                        <Input
                          value={row.name}
                          onChange={(e) =>
                            setLineItems((prev) =>
                              prev.map((item, i) => (i === index ? { ...item, name: e.target.value } : item)),
                            )
                          }
                          placeholder="e.g. Tuition fee"
                          className="h-9 border-[#dce3ec] text-[13px]"
                        />
                      </td>
                      <td className="px-3 py-2.5">
                        <Input
                          type="number"
                          min={0}
                          value={row.amount}
                          onChange={(e) =>
                            setLineItems((prev) =>
                              prev.map((item, i) =>
                                i === index ? { ...item, amount: Number(e.target.value) || 0 } : item,
                              ),
                            )
                          }
                          className="h-9 border-[#dce3ec] text-right text-[13px] tabular-nums"
                        />
                      </td>
                      <td className="px-3 py-2.5 text-center">
                        <button
                          type="button"
                          disabled={lineItems.length <= 1}
                          onClick={() => setLineItems((prev) => prev.filter((_, i) => i !== index))}
                          className="inline-flex size-8 items-center justify-center rounded-md text-[#9ca3af] hover:bg-[#fef2f2] hover:text-[#b91c1c] disabled:opacity-30"
                          aria-label="Remove fee head"
                        >
                          <Trash2Icon className="size-3.5" aria-hidden />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <CollegeAdminPanelChromeFooter className="justify-end gap-4">
              <span className="text-[13px] text-[#64748b]">
                Total{" "}
                <span className="font-semibold tabular-nums text-[#111827]">
                  ₹{total.toLocaleString("en-IN")}
                </span>
              </span>
            </CollegeAdminPanelChromeFooter>
          </CollegeAdminPanelShell>

          {formError ? (
            <p className="rounded-lg border border-[#fecaca] bg-[#fef2f2] px-3 py-2 text-[13px] text-[#b91c1c]">
              {formError}
            </p>
          ) : null}

          <div className="flex flex-wrap items-center justify-end gap-2 rounded-xl border border-[#e8ecf2] bg-white px-4 py-3.5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <CollegeAdminSecondaryButton
              disabled={save.isPending || publish.isPending}
              onClick={() => void persist(false)}
            >
              {data.save_draft_label}
            </CollegeAdminSecondaryButton>
            <CollegeAdminSecondaryButton
              disabled={save.isPending || publish.isPending}
              onClick={() => void persist(true)}
            >
              {data.publish_label}
            </CollegeAdminSecondaryButton>
            <CollegeAdminPrimaryButton
              disabled={save.isPending}
              onClick={() => {
                void (async () => {
                  const ok = await persist(false);
                  if (ok) flow.goForward();
                })();
              }}
            >
              {data.continue_label}
            </CollegeAdminPrimaryButton>
          </div>
        </div>
      ) : null}
    </QueryState>
  );
}