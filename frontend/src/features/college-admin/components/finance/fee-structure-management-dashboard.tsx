"use client";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";

import Link from "next/link";
import { useState } from "react";

import { InfoIcon } from "@/components/icons/erp/generated/info";
import { CollegeAdminPrimaryLink } from "@/features/college-admin/components/ui/college-admin-page-buttons";
import {
  CollegeAdminPanelEmptyState,
  CollegeAdminTablePanel,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useFeeStructureManagementPage } from "@/features/college-admin/hooks/use-fee-structure-management";
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
  data: NonNullable<ReturnType<typeof useFeeStructureManagementPage>["data"]>;
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

export function FeeStructureManagementDashboard() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useFeeStructureManagementPage({ page });

  const createHref = data?.create_fee_structure_href ?? "/college-admin/finance/fee-structure-management?create=1";
  const headers = data?.table_headers ?? [];

  return (
    <div className="space-y-5" data-figma-frame="160:2630">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Fee Structure Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Approved fee structures by programme and semester"}
          </p>
        </div>
        <CollegeAdminPrimaryLink href={createHref} className="shrink-0">
          <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={data?.create_fee_structure_label ?? "Create fee structure"} />
        </CollegeAdminPrimaryLink>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <CollegeAdminTablePanel
              title={data.structures_section_title}
              description={data.structures_count_label}
              footer={
                <>
                  <span>{data.showing_label}</span>
                  {data.pagination.total_pages > 0 ? (
                    <Pagination data={data} page={page} setPage={setPage} />
                  ) : null}
                </>
              }
            >
              {data.structures.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[44rem] text-left text-[13px]">
                    <thead>
                      <tr className="border-b border-[#f1f5f9] text-[11px] font-semibold uppercase tracking-wide text-[#94a3b8]">
                        {headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "pb-3 pt-4 font-medium",
                              index === 0 ? "px-5" : "pr-3",
                              index === headers.length - 1 ? "pr-5 text-right" : "",
                              header === "Total" ? "text-right" : "",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.structures.map((row) => (
                        <tr key={row.structure_id} className="transition-colors hover:bg-[#f8fafc]">
                          <td className="px-5 py-3.5 font-medium text-[#111827]">
                            <Link href={row.detail_href} className="hover:text-[#245dd8]">
                              {row.structure_label}
                            </Link>
                          </td>
                          <td className="py-3.5 pr-3 text-[#374151]">{row.year_label}</td>
                          <td className="py-3.5 pr-3 text-[#374151]">{row.programme_label}</td>
                          <td className="py-3.5 pr-3 text-right tabular-nums font-medium text-[#111827]">
                            {row.total_label}
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
                  iconSlug="wallet"
                  title="No fee structures yet"
                  description="Create a fee structure for each programme and semester. Published structures drive student fee assessments and demands."
                  action={
                    <CollegeAdminPrimaryLink href={createHref}>
                      <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={data.create_fee_structure_label} />
                    </CollegeAdminPrimaryLink>
                  }
                />
              )}
            </CollegeAdminTablePanel>

            <div className="flex gap-3 rounded-xl border border-[#bfdbfe] bg-[#eff6ff] px-4 py-3.5">
              <InfoIcon className="mt-0.5 size-4 shrink-0 text-[#2563eb]" aria-hidden />
              <div className="text-[13px] leading-relaxed text-[#1e40af]">
                <p className="font-semibold text-[#1d4ed8]">{data.info_notice_title}</p>
                <p className="mt-0.5 text-[#1e40af]">{data.info_notice_body}</p>
              </div>
            </div>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}