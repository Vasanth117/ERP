"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useMemo } from "react";

import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { YearsSemestersSubNav } from "@/features/college-admin/components/academics/years-semesters-sub-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useAcademicYearDetailsPage } from "@/features/college-admin/hooks/use-academic-year-details";
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

export function AcademicYearDetailsDashboard() {
  const searchParams = useSearchParams();
  const yearId = useMemo(() => searchParams.get("year_id") ?? "", [searchParams]);
  const { data, isLoading, isError, error, refetch } = useAcademicYearDetailsPage(yearId || null);

  if (!yearId) {
    return (
      <div className="rounded-xl border border-[#e8ecf2] bg-white p-6 text-sm text-[#6b7280]">
        Select an academic year from{" "}
        <Link
          href="/college-admin/academics/academic-year-management"
          className="font-medium text-[#245dd8] hover:underline"
        >
          Academic years
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
            <YearsSemestersSubNav
              items={[
                { key: "years", label: "Years", href: "/college-admin/academics/academic-year-management", active: true },
                { key: "semesters", label: "Semesters", href: data.manage_semesters_href, active: false },
                {
                  key: "calendar",
                  label: "Academic calendar",
                  href: "/college-admin/academics/academic-calendar-configuration",
                  active: false,
                },
              ]}
            />

            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="flex min-w-0 items-start gap-3">
                <Link
                  href={data.back_href}
                  className="inline-flex size-9 shrink-0 items-center justify-center rounded-md border border-[#e8ecf2] bg-white text-[#374151] hover:bg-[#f9fafb]"
                  aria-label={data.back_label}
                >
                  <ChevronLeftIcon className="size-5" />
                </Link>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{data.page_title}</h2>
                    <StatusPill label={data.status_label} tone={data.status_tone} />
                    {data.is_current ? (
                      <span className="rounded-full bg-[#eff6ff] px-2 py-0.5 text-[11px] font-medium text-[#1d4ed8]">
                        Current year
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-1 text-[14px] text-[#6b7280]">{data.page_subtitle}</p>
                </div>
              </div>
              <Link
                href={data.manage_semesters_href}
                className="inline-flex h-9 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
              >
                {data.manage_semesters_label}
              </Link>
            </div>

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.terms_section_title}</h3>
                </div>
                {data.term_rows.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[24rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {data.terms_table_headers.map((h, i) => (
                            <th key={h} className={cn("pb-3 font-medium", i === 0 ? "px-5" : "pr-3")}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.term_rows.map((row) => (
                          <tr key={row.term_id} className="hover:bg-[#f9fafb]">
                            <td className="px-5 py-3 font-medium text-[#111827]">{row.label}</td>
                            <td className="py-3 pr-3 text-[#374151]">{row.period_label}</td>
                            <td className="py-3 pr-5">
                              <StatusPill label={row.status_label} tone={row.status_tone} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-8 text-sm text-[#9ca3af]">No terms configured yet.</p>
                )}
              </section>

              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.overview_section_title}</h3>
                </div>
                <dl className="divide-y divide-[#f1f5f9] px-5">
                  {data.overview_rows.map((row) => (
                    <div key={row.key} className="flex justify-between gap-4 py-3 text-[13px]">
                      <dt className="text-[#6b7280]">{row.label}</dt>
                      <dd className="text-right font-medium text-[#111827]">{row.value}</dd>
                    </div>
                  ))}
                </dl>
              </section>
            </div>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}