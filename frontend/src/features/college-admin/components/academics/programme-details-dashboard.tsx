"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useMemo } from "react";

import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import {
  CollegeAdminPanelChromeHeader,
  CollegeAdminPanelShell,
  CollegeAdminSidePanel,
  CollegeAdminTablePanel,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useProgrammeDetailsPage } from "@/features/college-admin/hooks/use-programme-details";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      {label}
    </span>
  );
}

export function ProgrammeDetailsDashboard() {
  const searchParams = useSearchParams();
  const programmeId = useMemo(() => searchParams.get("programme_id") ?? "", [searchParams]);
  const { data, isLoading, isError, error, refetch } = useProgrammeDetailsPage(programmeId || null);

  if (!programmeId) {
    return (
      <div className="rounded-2xl border border-[#e5e7eb] bg-white p-6 text-sm text-[#64748b]">
        Open a programme from{" "}
        <Link href="/college-admin/academics/programme-management" className="font-semibold text-[#245dd8] hover:underline">
          Programme management
        </Link>
        .
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="flex min-w-0 items-start gap-3">
                <Link
                  href={data.back_href}
                  className="inline-flex size-9 shrink-0 items-center justify-center rounded-md border border-[#e5e7eb] bg-white text-[#374151] hover:bg-[#f9fafb]"
                  aria-label="Back"
                >
                  <ChevronLeftIcon className="size-5" />
                </Link>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{data.programme_name}</h2>
                    <StatusPill label={data.status_label} tone={data.status_tone} />
                  </div>
                  <p className="mt-1 font-mono text-[13px] text-[#64748b]">{data.programme_code}</p>
                  <p className="mt-1 text-[14px] text-[#6b7280]">{data.page_subtitle}</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
              <div className="space-y-5">
                <CollegeAdminTablePanel title="Programme profile">
                  <dl className="divide-y divide-[#f1f5f9] px-5 py-2">
                    {data.summary_rows.map((row) => (
                      <div key={row.label} className="flex justify-between gap-4 py-3 text-[13px]">
                        <dt className="text-[#64748b]">{row.label}</dt>
                        <dd className="max-w-[65%] text-right font-medium text-[#111827]">{row.value}</dd>
                      </div>
                    ))}
                  </dl>
                </CollegeAdminTablePanel>

                {data.description ? (
                  <CollegeAdminPanelShell>
                    <CollegeAdminPanelChromeHeader title="Description" />
                    <p className="px-5 py-4 text-[13px] leading-relaxed text-[#374151]">{data.description}</p>
                  </CollegeAdminPanelShell>
                ) : null}

                <p className="text-[12px] text-[#94a3b8]">{data.edit_note}</p>
              </div>

              <aside className="space-y-5">
                <CollegeAdminSidePanel title={data.checklist_title}>
                  <ul className="space-y-3">
                    {data.checklist_items.map((item) => (
                      <li key={item.key} className="flex gap-3">
                        <span
                          className={cn(
                            "mt-1.5 size-2.5 shrink-0 rounded-full",
                            item.enabled ? "bg-[#10b981]" : "bg-[#e5e7eb]",
                          )}
                          aria-hidden
                        />
                        <div>
                          <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
                          <p className="text-[12px] text-[#64748b]">{item.description}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                </CollegeAdminSidePanel>

                <CollegeAdminSidePanel title={data.linked_title}>
                  <ul className="space-y-2">
                    {data.linked_items.map((item) => (
                      <li key={item.key}>
                        <Link
                          href={item.href}
                          className="block rounded-lg border border-transparent px-2 py-2.5 transition-colors hover:border-[#dbeafe] hover:bg-[#f8fbff]"
                        >
                          <p className="text-[13px] font-semibold text-[#111827]">{item.title}</p>
                          <p className="text-[12px] text-[#64748b]">{item.description}</p>
                        </Link>
                      </li>
                    ))}
                  </ul>
                </CollegeAdminSidePanel>
              </aside>
            </div>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}