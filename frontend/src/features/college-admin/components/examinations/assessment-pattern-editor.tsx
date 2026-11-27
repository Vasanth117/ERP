"use client";

import { Trash2Icon } from "@/components/icons/erp/generated/trash-2";
import {
  CollegeAdminPrimaryButton,
  CollegeAdminSecondaryButton,
} from "@/features/college-admin/components/ui/college-admin-action-button";
import type { InternalExternalAssessmentComponentDraft } from "@/features/college-admin/types/internal-external-assessment";
import { cn } from "@/lib/utils";

function newComponentDraft(index: number): InternalExternalAssessmentComponentDraft {
  return {
    component_id: `new-${Date.now()}-${index}`,
    code: `COMP${index}`,
    name: "",
    assessment_type: "cia",
    weight_percent: 0,
    max_marks: 50,
    source: "faculty",
  };
}

const inputClass =
  "h-9 w-full min-w-0 rounded-md border border-[#dce3ec] bg-white px-2 text-[13px] text-[#374151]";
const selectClass =
  "h-9 w-full min-w-0 rounded-md border border-[#dce3ec] bg-white px-2 text-[13px] text-[#374151]";

export function AssessmentPatternEditor({
  components,
  assessmentTypeOptions,
  sourceOptions,
  addLabel,
  onChange,
}: {
  components: InternalExternalAssessmentComponentDraft[];
  assessmentTypeOptions: { value: string; label: string }[];
  sourceOptions: { value: string; label: string }[];
  addLabel: string;
  onChange: (next: InternalExternalAssessmentComponentDraft[]) => void;
}) {
  const totalWeight = components.reduce((sum, row) => sum + (Number(row.weight_percent) || 0), 0);
  const weightOk = Math.abs(totalWeight - 100) < 0.05;

  const updateRow = (index: number, patch: Partial<InternalExternalAssessmentComponentDraft>) => {
    onChange(components.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  };

  const removeRow = (index: number) => {
    onChange(components.filter((_, i) => i !== index));
  };

  const addRow = () => {
    onChange([...components, newComponentDraft(components.length + 1)]);
  };

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#f1f5f9] px-5 py-3">
        <p className="text-[12px] text-[#6b7280]">Define components and weightage for this academic year and semester.</p>
        <CollegeAdminSecondaryButton type="button" onClick={addRow}>
          {addLabel}
        </CollegeAdminSecondaryButton>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[36rem] text-left text-[13px]">
          <thead>
            <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
              <th className="pl-5 py-3 pr-2 font-medium">Component</th>
              <th className="px-2 py-3 font-medium">Type</th>
              <th className="px-2 py-3 font-medium">Weight %</th>
              <th className="px-2 py-3 font-medium">Max marks</th>
              <th className="px-2 py-3 font-medium">Source</th>
              <th className="pr-5 py-3 font-medium">
                <span className="sr-only">Remove</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#f1f5f9]">
            {components.map((row, index) => (
              <tr key={row.component_id || `${row.code}-${index}`}>
                <td className="pl-5 py-2.5 pr-2">
                  <input
                    className={inputClass}
                    aria-label="Component name"
                    value={row.name}
                    placeholder="e.g. End semester"
                    onChange={(e) => updateRow(index, { name: e.target.value })}
                  />
                </td>
                <td className="px-2 py-2.5">
                  <select
                    className={selectClass}
                    aria-label="Assessment type"
                    value={row.assessment_type}
                    onChange={(e) => updateRow(index, { assessment_type: e.target.value })}
                  >
                    {assessmentTypeOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-2 py-2.5">
                  <input
                    className={cn(inputClass, "tabular-nums")}
                    type="number"
                    min={0}
                    max={100}
                    step={1}
                    aria-label="Weight percent"
                    value={row.weight_percent}
                    onChange={(e) => updateRow(index, { weight_percent: Number(e.target.value) || 0 })}
                  />
                </td>
                <td className="px-2 py-2.5">
                  <input
                    className={cn(inputClass, "tabular-nums")}
                    type="number"
                    min={1}
                    step={1}
                    aria-label="Max marks"
                    value={row.max_marks}
                    onChange={(e) => updateRow(index, { max_marks: Number(e.target.value) || 0 })}
                  />
                </td>
                <td className="px-2 py-2.5">
                  <select
                    className={selectClass}
                    aria-label="Source"
                    value={row.source}
                    onChange={(e) => updateRow(index, { source: e.target.value })}
                  >
                    {sourceOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="pr-5 py-2.5">
                  <button
                    type="button"
                    className="inline-flex size-8 items-center justify-center rounded-md text-[#9ca3af] hover:bg-[#fef2f2] hover:text-[#b91c1c] disabled:opacity-40"
                    disabled={components.length <= 1}
                    aria-label="Remove component"
                    onClick={() => removeRow(index)}
                  >
                    <Trash2Icon className="size-4" aria-hidden />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t border-[#f1f5f9]">
              <td className="pl-5 py-3 font-semibold text-[#111827]">
                Total {totalWeight.toFixed(totalWeight % 1 === 0 ? 0 : 1)}%
              </td>
              <td colSpan={4}>
                {!weightOk ? (
                  <p className="text-[12px] text-[#b45309]">Weights must add up to 100% before you continue.</p>
                ) : (
                  <p className="text-[12px] text-[#047857]">Weightage is balanced.</p>
                )}
              </td>
              <td />
            </tr>
          </tfoot>
        </table>
      </div>
      {components.length === 0 ? (
        <div className="flex justify-center px-5 py-8">
          <CollegeAdminPrimaryButton type="button" onClick={addRow}>
            {addLabel}
          </CollegeAdminPrimaryButton>
        </div>
      ) : null}
    </div>
  );
}