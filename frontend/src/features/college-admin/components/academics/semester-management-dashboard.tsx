"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { YearsSemestersSubNav } from "@/features/college-admin/components/academics/years-semesters-sub-nav";
import {
  CollegeAdminPrimaryLink,
  CollegeAdminSecondaryButton,
} from "@/features/college-admin/components/ui/college-admin-action-button";
import {
  CollegeAdminPanelEmptyState,
  CollegeAdminSidePanel,
  CollegeAdminTablePanel,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useSemesterManagementPage } from "@/features/college-admin/hooks/use-semester-management";
import type { SemesterManagementTableRow } from "@/features/college-admin/types/semester-management";
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

export function SemesterManagementDashboard() {
  const searchParams = useSearchParams();
  const initialYearId =
    searchParams.get("academic_year_id") ?? searchParams.get("year_id") ?? undefined;

  const [yearId, setYearId] = useState(initialYearId);

  const { data, isLoading, isError, error, refetch } = useSemesterManagementPage({
    academic_year_id: yearId,
  });

  useEffect(() => {
    if (data?.selected_academic_year_id) setYearId(data.selected_academic_year_id);
  }, [data?.selected_academic_year_id]);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `semester-management-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const createHref = yearId
    ? `/college-admin/academics/create-semester?academic_year_id=${encodeURIComponent(yearId)}`
    : "/college-admin/academics/create-semester";

  return (
    <div className="space-y-5" data-figma-frame="69:140138">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Semester Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Configure semesters, teaching periods and academic milestones"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <CollegeAdminSecondaryButton onClick={handleExport} disabled={isLoading || !data}>
            <CollegeAdminDownload className="size-3.5" aria-hidden />
            {data?.export_label ?? "Export"}
          </CollegeAdminSecondaryButton>
          <CollegeAdminPrimaryLink href={createHref}>
            <PlusIcon className="size-3.5" aria-hidden />
            {data?.new_semester_label ?? "New semester"}
          </CollegeAdminPrimaryLink>
        </div>
      </div>

      {data?.sub_nav?.length ? <YearsSemestersSubNav items={data.sub_nav} /> : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <YearFilterBar data={data} yearId={yearId} setYearId={setYearId} />

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
              <SemesterTable data={data} yearId={yearId} createHref={createHref} newSemesterLabel={data.new_semester_label} />
              <aside className="space-y-5">
                <ProgressSidebar data={data} />
                <LinkedSidebar data={data} />
              </aside>
            </div>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}

function YearFilterBar({
  data,
  yearId,
  setYearId,
}: {
  data: NonNullable<ReturnType<typeof useSemesterManagementPage>["data"]>;
  yearId: string | undefined;
  setYearId: (v: string | undefined) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <select
        aria-label="Academic year"
        value={yearId ?? ""}
        onChange={(e) => setYearId(e.target.value || undefined)}
        className="h-9 min-w-[12rem] rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]"
      >
        {data.year_filter_options.map((opt) => (
          <option key={`${opt.value}-${opt.label}`} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function SemesterTable({
  data,
  yearId,
  createHref,
  newSemesterLabel,
}: {
  data: NonNullable<ReturnType<typeof useSemesterManagementPage>["data"]>;
  yearId: string | undefined;
  createHref: string;
  newSemesterLabel: string;
}) {
  return (
    <CollegeAdminTablePanel
      title={data.semesters_panel_title}
      footer={
        <>
          <span>{data.semester_count_label}</span>
          <Link
            href={data.manage_terms_href}
            className="font-semibold text-[#245dd8] transition-colors hover:text-[#1f4fb8] hover:underline"
          >
            {data.manage_terms_label}
          </Link>
        </>
      }
    >
      {data.semester_rows.length ? (
        <SemesterTableBody data={data} yearId={yearId} />
      ) : (
        <CollegeAdminPanelEmptyState
          iconSlug="layers"
          title="No semesters yet"
          description="Create odd and even semesters for this academic year, then set teaching dates, exams, and registration windows."
          action={
            <CollegeAdminPrimaryLink href={createHref}>
              <PlusIcon className="size-3.5" aria-hidden />
              {newSemesterLabel}
            </CollegeAdminPrimaryLink>
          }
        />
      )}
    </CollegeAdminTablePanel>
  );
}

function SemesterTableBody({
  data,
  yearId,
}: {
  data: NonNullable<ReturnType<typeof useSemesterManagementPage>["data"]>;
  yearId: string | undefined;
}) {
  const detailHref = (row: SemesterManagementTableRow) => {
    const q = new URLSearchParams({ term_id: row.term_id });
    if (yearId) q.set("academic_year_id", yearId);
    return `/college-admin/academics/semester-details?${q.toString()}`;
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[36rem] text-left text-[13px]">
        <thead>
          <tr className="border-b border-[#f1f5f9] text-[11px] font-semibold uppercase tracking-wide text-[#94a3b8]">
            {data.table_headers.map((header, index) => (
              <th key={header} className={cn("pb-3 pt-4 font-medium", index === 0 ? "px-5" : "pr-3")}>
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[#f1f5f9]">
          {data.semester_rows.map((row) => (
            <tr key={row.term_id} className="transition-colors hover:bg-[#f8fafc]">
              <td className="px-5 py-3.5 font-medium text-[#111827]">
                <Link href={detailHref(row)} className="hover:text-[#245dd8]">
                  {row.label}
                </Link>
              </td>
              <td className="py-3 pr-3 text-[#374151]">{row.period_label}</td>
              <td className="py-3 pr-3 text-[#374151]">{row.week_label}</td>
              <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.course_count}</td>
              <td className="py-3 pr-5">
                <StatusPill label={row.status_label} tone={row.status_tone} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProgressSidebar({ data }: { data: NonNullable<ReturnType<typeof useSemesterManagementPage>["data"]> }) {
  return (
    <CollegeAdminSidePanel title={data.progress_section_title}>
      {data.progress_items.length ? (
        <ul className="space-y-4">
          {data.progress_items.map((item) => (
            <li key={item.key}>
              <div className="mb-1.5 flex justify-between text-[13px]">
                <span className="font-medium text-[#111827]">{item.label}</span>
                <span className="tabular-nums text-[#64748b]">{item.progress_percent}%</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-[#e8ecf2]">
                <div className="h-full rounded-full bg-[#245dd8]" style={{ width: `${Math.min(100, item.progress_percent)}%` }} />
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-[13px] leading-relaxed text-[#94a3b8]">Open a semester from the table to track setup progress.</p>
      )}
    </CollegeAdminSidePanel>
  );
}

function LinkedSidebar({ data }: { data: NonNullable<ReturnType<typeof useSemesterManagementPage>["data"]> }) {
  return (
    <CollegeAdminSidePanel title={data.linked_section_title}>
      <ul className="divide-y divide-[#f1f5f9]">
        {data.linked_items.map((item) => (
          <li key={item.key} className="flex items-start justify-between gap-3 py-3 first:pt-0 last:pb-0">
            <div className="min-w-0">
              <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
              <p className="text-[12px] text-[#64748b]">{item.subtitle}</p>
            </div>
            <StatusPill label={item.status_label} tone={item.status_tone} />
          </li>
        ))}
      </ul>
    </CollegeAdminSidePanel>
  );
}