"use client";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ShuffleIcon } from "@/components/icons/erp/generated/shuffle";
import { Input } from "@/components/ui/input";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useCreateRegulationManagement,
  useRegulationManagementPage,
} from "@/features/college-admin/hooks/use-regulation-management";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
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


export function RegulationManagementDashboard() {
  const [selectedCode, setSelectedCode] = useState<string | undefined>();
  const [showCreate, setShowCreate] = useState(false);
  const [newCode, setNewCode] = useState("");
  const [newLabel, setNewLabel] = useState("");

  const { data, isLoading, isError, error, refetch } = useRegulationManagementPage(selectedCode);
  const createReg = useCreateRegulationManagement();

  useEffect(() => {
    if (data?.selected_regulation_code) setSelectedCode(data.selected_regulation_code);
  }, [data?.selected_regulation_code]);

  const handleCreate = () => {
    if (!newCode.trim()) return;
    createReg.mutate(
      { regulation_code: newCode.trim(), display_label: newLabel.trim() || null },
      {
        onSuccess: (page) => {
          setShowCreate(false);
          setNewCode("");
          setNewLabel("");
          setSelectedCode(page.selected_regulation_code);
        },
      },
    );
  };

  return (
    <div className="space-y-5" data-figma-frame="69:141649">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold text-[#111827]">{data?.page_title ?? "Regulation Management"}</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            href={data?.compare_href ?? "/college-admin/academics/academic-configuration-history"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            <ShuffleIcon className="size-3.5" />
            {data?.compare_label ?? "Compare regulations"}
          </Link>
          <button
            type="button"
            onClick={() => setShowCreate((v) => !v)}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={data?.new_regulation_label ?? "New regulation" } />
          </button>
        </div>
      </div>

      {showCreate ? (
        <section className="flex flex-wrap items-end gap-3 rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-sm">
          <div>
            <label className="text-[12px] text-[#374151]">Regulation code *</label>
            <Input className="mt-1 h-9 w-40" value={newCode} onChange={(e) => setNewCode(e.target.value)} placeholder="R2027" />
          </div>
          <div className="min-w-[12rem] flex-1">
            <label className="text-[12px] text-[#374151]">Display label</label>
            <Input className="mt-1 h-9" value={newLabel} onChange={(e) => setNewLabel(e.target.value)} placeholder="Optional title" />
          </div>
          <button
            type="button"
            disabled={createReg.isPending}
            onClick={handleCreate}
            className="h-9 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white disabled:opacity-50"
          >
            Create draft
          </button>
        </section>
      ) : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <div className="grid gap-5 xl:grid-cols-3">
            <div className="space-y-5 xl:col-span-2">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-sm">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.regulations_section_title}</h3>
                </div>
                {data.regulations.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[40rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] uppercase tracking-wide text-[#9ca3af]">
                          {data.table_headers.map((h, i) => (
                            <th key={h} className={cn("pb-3 pt-4 font-medium", i === 0 ? "px-5" : "pr-3")}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.regulations.map((row) => (
                          <tr
                            key={row.regulation_id}
                            className={cn(
                              "cursor-pointer hover:bg-[#f9fafb]",
                              row.is_selected && "bg-[#f0f6ff]",
                            )}
                            onClick={() => setSelectedCode(row.regulation_code)}
                          >
                            <td className="px-5 py-3 font-semibold text-[#111827]">{row.regulation_label}</td>
                            <td className="py-3 pr-3 text-[#374151]">{row.effective_from_label}</td>
                            <td className="py-3 pr-3 text-[#374151]">{row.batch_range_label}</td>
                            <td className="py-3 pr-3 tabular-nums">{row.student_count.toLocaleString("en-IN")}</td>
                            <td className="py-3 pr-3 tabular-nums">{row.programme_count}</td>
                            <td className="py-3 pr-5">
                              <StatusPill label={row.status_label} tone={row.status_tone} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-8 text-sm text-[#9ca3af]">No regulations found. Add curriculum references or create a new regulation.</p>
                )}
                <div className="flex justify-between border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  <span>{data.regulations_count_label}</span>
                  <Link href={data.view_documents_href} className="font-medium text-[#245dd8] hover:underline">
                    {data.view_documents_label}
                  </Link>
                </div>
              </section>

              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-sm">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.highlights_section_title}</h3>
                {data.highlight_rows.length ? (
                  <dl className="mt-4 grid gap-4 sm:grid-cols-2">
                    {data.highlight_rows.map((row) => (
                      <div key={row.key}>
                        <dt className="text-[12px] text-[#9ca3af]">{row.label}</dt>
                        <dd className="text-[13px] font-medium text-[#111827]">{row.value}</dd>
                      </div>
                    ))}
                  </dl>
                ) : (
                  <p className="mt-3 text-sm text-[#9ca3af]">Select a regulation to view highlights.</p>
                )}
              </section>
            </div>

            <div className="space-y-4">
              {data.phase_out_steps.length ? (
                <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-sm">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.phase_out_section_title}</h3>
                  <ul className="mt-4 space-y-4 border-l border-[#e5e7eb] pl-4">
                    {data.phase_out_steps.map((step) => (
                      <li key={step.step_id} className="relative pl-2">
                        <span
                          className={cn(
                            "absolute -left-[21px] top-1.5 size-2.5 rounded-full ring-4 ring-white",
                            step.is_active ? "bg-[#3b82f6]" : "bg-[#d1d5db]",
                          )}
                        />
                        <p className="text-[13px] font-medium text-[#111827]">{step.title}</p>
                        <p className="text-[12px] text-[#6b7280]">{step.date_label}</p>
                      </li>
                    ))}
                  </ul>
                </section>
              ) : null}

              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-sm">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.documents_section_title}</h3>
                {data.documents.length ? (
                  <ul className="mt-4 space-y-3">
                    {data.documents.map((doc) => (
                      <li key={doc.document_id} className="flex items-start justify-between gap-2 text-[13px]">
                        <div>
                          <p className="font-medium text-[#111827]">{doc.title}</p>
                          <p className="text-[11px] text-[#9ca3af]">{doc.size_label}</p>
                        </div>
                        {doc.download_href ? (
                          <Link href={doc.download_href} className="shrink-0 text-[12px] font-medium text-[#245dd8] hover:underline">
                            {doc.download_label}
                          </Link>
                        ) : (
                          <span className="text-[12px] text-[#9ca3af]">{doc.download_label}</span>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-3 text-sm text-[#9ca3af]">No documents attached for this regulation.</p>
                )}
              </section>
            </div>

          </div>
        ) : null}
      </QueryState>
    </div>
  );
}