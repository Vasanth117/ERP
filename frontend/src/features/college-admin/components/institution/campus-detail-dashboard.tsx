"use client";

import Link from "next/link";
import { CollegeAdminDashboardPanel as Panel } from "@/features/college-admin/components/ui/dashboard-panel-ui";

import {
  getCollegeAdminErpIcon,
  resolveCollegeAdminIconSlug,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useCampusDetailPage } from "@/features/college-admin/hooks/use-institution";
import type { CampusFacilityStatusRow, CampusSummaryStat } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";


function SummaryGrid({ stats }: { stats: CampusSummaryStat[] }) {
  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-4 py-2">
      {stats.map((row) => (
        <div key={row.key}>
          <dt className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
            {row.label}
          </dt>
          <dd className="mt-1 text-[15px] font-semibold tabular-nums text-[#111827]">
            {row.value}
          </dd>
        </div>
      ))}
    </dl>
  );
}

function FacilityOpenBadge({ row }: { row: CampusFacilityStatusRow }) {
  const open = row.status_code === "open";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium",
        open ? "bg-[#ecfdf5] text-[#047857]" : "bg-[#f3f4f6] text-[#6b7280]",
      )}
    >
      <span className={cn("size-1.5 rounded-full", open ? "bg-[#10b981]" : "bg-[#9ca3af]")} />
      {row.status_label}
    </span>
  );
}

export function CampusDetailDashboard({ campusId }: { campusId: string }) {
  const { data, isLoading, isError, error, refetch } = useCampusDetailPage(campusId);

  return (
    <div className="space-y-5" data-figma-frame="72:7582">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <Link
            href={data?.back_href ?? "/college-admin/institution/campuses"}
            className="text-[12px] font-medium text-[#245dd8] hover:underline"
          >
            ← Campuses
          </Link>
          <h2 className="mt-1 text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Campus details"}
          </h2>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href={`/college-admin/institution/campuses/new?campus_id=${encodeURIComponent(campusId)}`}
            className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            Edit campus
          </Link>
          <Link
            href={data?.contact_href ?? "/college-admin/institution/campuses"}
            className="inline-flex h-9 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            Address & contact →
          </Link>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
            <Panel
              title="Buildings"
              actionHref={data.manage_buildings_href}
              actionLabel="Manage buildings →"
            >
              {data.buildings.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[36rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        <th className="pb-3 pr-3 font-medium">Building</th>
                        <th className="pb-3 pr-3 font-medium">Floors</th>
                        <th className="pb-3 pr-3 font-medium">Classrooms</th>
                        <th className="pb-3 pr-3 font-medium">Labs</th>
                        <th className="pb-3 font-medium">Departments</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.buildings.map((row) => (
                        <tr key={row.building_id}>
                          <td className="py-3 pr-3 font-medium text-[#111827]">{row.name}</td>
                          <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.floors}</td>
                          <td className="py-3 pr-3 tabular-nums">{row.classroom_count}</td>
                          <td className="py-3 pr-3 tabular-nums">{row.laboratory_count}</td>
                          <td className="py-3 text-[#374151]">{row.departments_label}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="py-6 text-sm text-[#9ca3af]">
                  No buildings registered for this campus yet. Use manage buildings to add them.
                </p>
              )}
              <div className="flex items-center justify-between border-t border-[#f1f5f9] py-3 text-[12px] text-[#6b7280]">
                <span>{data.buildings_footer_label}</span>
                {data.buildings_total > data.buildings_shown ? (
                  <Link
                    href={data.view_all_buildings_href}
                    className="font-medium text-[#245dd8] hover:underline"
                  >
                    View all →
                  </Link>
                ) : null}
              </div>
            </Panel>

            <div className="space-y-5">
              <Panel title="Campus summary">
                <SummaryGrid stats={data.summary_stats} />
              </Panel>

              <Panel title="Facilities">
                {data.facility_statuses.length ? (
                  <ul className="divide-y divide-[#f1f5f9]">
                    {data.facility_statuses.map((item) => {
                      const Icon =
                        getCollegeAdminErpIcon(resolveCollegeAdminIconSlug(item.icon_slug)) ??
                        getCollegeAdminErpIcon("landmark");
                      return (
                        <li
                          key={item.showcase_id}
                          className="flex items-start justify-between gap-2 py-3.5 first:pt-2"
                        >
                          <div className="flex min-w-0 gap-3">
                            {Icon ? (
                              <Icon className="mt-0.5 size-[18px] shrink-0 text-[#9ca3af]" aria-hidden />
                            ) : null}
                            <div>
                              <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
                              <p className="text-[12px] text-[#6b7280]">{item.subtitle}</p>
                            </div>
                          </div>
                          <FacilityOpenBadge row={item} />
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <p className="py-4 text-sm text-[#9ca3af]">No campus facilities on file.</p>
                )}
              </Panel>
            </div>
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}