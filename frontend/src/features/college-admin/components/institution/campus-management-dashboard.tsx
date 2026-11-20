"use client";

import Link from "next/link";
import { useCallback, useEffect, useId, useState, type ReactNode } from "react";

import { LandmarkIcon } from "@/components/icons/erp/generated/landmark";
import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  CollegeAdminDownload,
  getCollegeAdminErpIcon,
  resolveCollegeAdminIconSlug,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useCampusManagementDashboard,
  useCreateCampus,
} from "@/features/college-admin/hooks/use-institution";
import type {
  CampusDashboardKpi,
  CampusOpenIssue,
  ClassroomUtilizationBar,
} from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function kpiHintClass(tone: string) {
  if (tone === "success") return "text-[#059669]";
  if (tone === "warning") return "text-[#d97706]";
  return "text-[#6b7280]";
}

function KpiCard({ kpi }: { kpi: CampusDashboardKpi }) {
  return (
    <div className="flex min-h-[7.25rem] flex-col rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <p className="text-[12px] font-medium text-[#6b7280]">{kpi.label}</p>
      <p className="mt-3 text-[1.75rem] font-bold tabular-nums text-[#111827]">
        {kpi.value}
      </p>
      <p className={cn("mt-auto pt-3 text-[12px]", kpiHintClass(kpi.hint_tone))}>
        {kpi.hint}
      </p>
    </div>
  );
}

function Panel({
  title,
  children,
  actionHref,
  actionLabel,
}: {
  title: string;
  children: ReactNode;
  actionHref?: string;
  actionLabel?: string;
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="flex items-center justify-between gap-2 border-b border-[#f1f5f9] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
        {actionHref && actionLabel ? (
          <Link
            href={actionHref}
            className="text-[12px] font-medium text-[#245dd8] hover:underline"
          >
            {actionLabel}
          </Link>
        ) : null}
      </div>
      <div className="px-5 py-1">{children}</div>
    </section>
  );
}

function StatusPill({ label, active }: { label: string; active: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium",
        active
          ? "bg-[#ecfdf5] text-[#047857]"
          : "bg-[#f3f4f6] text-[#6b7280]",
      )}
    >
      <span
        className={cn(
          "size-1.5 rounded-full",
          active ? "bg-[#10b981]" : "bg-[#9ca3af]",
        )}
      />
      {label}
    </span>
  );
}

function UtilizationChart({ bars }: { bars: ClassroomUtilizationBar[] }) {
  const max = Math.max(...bars.map((b) => b.utilization_percent), 1);
  if (!bars.length) {
    return (
      <p className="py-6 text-sm text-[#9ca3af]">
        No classroom utilisation data registered yet.
      </p>
    );
  }
  return (
    <div className="flex h-52 items-end justify-between gap-2 overflow-x-auto pb-2 pt-4">
      {bars.map((bar) => (
        <div
          key={bar.building_label}
          className="flex min-w-[3rem] flex-1 flex-col items-center gap-1.5"
        >
          <span className="text-[11px] font-semibold tabular-nums text-[#374151]">
            {bar.utilization_percent}%
          </span>
          <div
            className={cn(
              "w-full max-w-[48px] rounded-t-md",
              bar.tone === "warning" ? "bg-[#f97316]" : "bg-[#245dd8]",
            )}
            style={{
              height: `${Math.max(12, (bar.utilization_percent / max) * 100)}%`,
            }}
          />
          <span className="max-w-[4.5rem] text-center text-[10px] leading-tight text-[#6b7280]">
            {bar.building_label}
          </span>
        </div>
      ))}
    </div>
  );
}

function IssueBadge({ issue }: { issue: CampusOpenIssue }) {
  const styles =
    issue.tone === "info"
      ? "bg-[#eff6ff] text-[#1d4ed8]"
      : "bg-[#fff7ed] text-[#c2410c]";
  const dot = issue.tone === "info" ? "bg-[#3b82f6]" : "bg-[#f97316]";
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium",
        styles,
      )}
    >
      <span className={cn("size-1.5 rounded-full", dot)} />
      {issue.status_label}
    </span>
  );
}

function formatSnapshot(iso: string) {
  try {
    return new Intl.DateTimeFormat("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Asia/Kolkata",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function CampusManagementDashboard() {
  const { data, isLoading, isError, error, refetch } =
    useCampusManagementDashboard();
  const create = useCreateCampus();
  const [addOpen, setAddOpen] = useState(false);
  const [campusCode, setCampusCode] = useState("");
  const [campusName, setCampusName] = useState("");
  const codeId = useId();
  const nameId = useId();

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.location.hash === "#add-campus") {
      setAddOpen(true);
    }
  }, []);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `campus-management-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const submitCreate = () => {
    if (!campusCode.trim() || !campusName.trim()) return;
    create.mutate(
      { campus_code: campusCode.trim(), name: campusName.trim(), is_main: false },
      {
        onSuccess: (campus) => {
          setAddOpen(false);
          setCampusCode("");
          setCampusName("");
          if (typeof window !== "undefined" && window.location.hash) {
            window.history.replaceState(null, "", window.location.pathname);
          }
          window.location.href = campus.campus_id
            ? `/college-admin/institution/campuses/${campus.campus_id}`
            : "/college-admin/institution/campuses";
        },
      },
    );
  };

  return (
    <div className="space-y-5" data-figma-frame="72:7199">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Campus Management Dashboard"}
          </h2>
          <p className="mt-1 max-w-2xl text-[14px] leading-relaxed text-[#6b7280]">
            {data?.page_subtitle ??
              "Overview of all campuses, capacity and facilities"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] bg-white text-xs font-medium text-[#374151]"
            onClick={handleExport}
            disabled={isLoading || !data}
          >
            <CollegeAdminDownload className="size-3.5" />
            {data?.export_label ?? "Export"}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
            onClick={() => setAddOpen(true)}
            disabled={!data}
          >
            <PlusIcon className="size-3.5" aria-hidden />
            {data?.add_campus_label ?? "Add campus"}
          </Button>
        </div>
      </div>

      <QueryState
        isLoading={isLoading}
        isError={isError}
        error={error}
        onRetry={() => void refetch()}
      >
        {data ? (
          <>
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {data.kpis.map((kpi) => (
                <KpiCard key={kpi.key} kpi={kpi} />
              ))}
            </div>

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_392px]">
              <div className="space-y-5">
                <Panel
                  title="Campuses"
                  actionHref={data.campuses_view_all_href}
                  actionLabel="View all →"
                >
                  {data.campuses.length ? (
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[32rem] text-left text-[13px]">
                        <thead>
                          <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                            <th className="pb-3 pr-4 font-medium">Campus</th>
                            <th className="pb-3 pr-4 font-medium">Location</th>
                            <th className="pb-3 pr-4 font-medium">Students</th>
                            <th className="pb-3 pr-4 font-medium">Buildings</th>
                            <th className="pb-3 font-medium">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#f1f5f9]">
                          {data.campuses.map((row) => (
                            <tr key={row.campus_id} className="text-[#374151]">
                              <td className="py-3 pr-4 font-medium text-[#111827]">
                                <Link
                                  href={row.detail_href}
                                  className="hover:text-[#245dd8] hover:underline"
                                >
                                  {row.name}
                                </Link>
                              </td>
                              <td className="py-3 pr-4">{row.location_label}</td>
                              <td className="py-3 pr-4 tabular-nums">
                                {row.student_count.toLocaleString("en-IN")}
                              </td>
                              <td className="py-3 pr-4 tabular-nums">
                                {row.buildings_count}
                              </td>
                              <td className="py-3">
                                <StatusPill
                                  label={row.status_label}
                                  active={row.status_code === "active"}
                                />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="py-4 text-sm text-[#9ca3af]">No campuses yet.</p>
                  )}
                  <div className="flex items-center justify-between border-t border-[#f1f5f9] py-3 text-[12px] text-[#6b7280]">
                    <span>{data.campus_count_label}</span>
                    <Link
                      href={data.campus_details_href}
                      className="font-medium text-[#245dd8] hover:underline"
                    >
                      Campus details →
                    </Link>
                  </div>
                </Panel>

                <Panel title="Classroom utilisation by building">
                  <UtilizationChart bars={data.classroom_utilization} />
                  {data.classroom_utilization_hint ? (
                    <p className="border-t border-[#f1f5f9] py-3 text-[12px] text-[#6b7280]">
                      {data.classroom_utilization_hint}
                    </p>
                  ) : null}
                </Panel>
              </div>

              <div className="space-y-5">
                <Panel title="Facilities">
                  <ul className="divide-y divide-[#f1f5f9]">
                    {data.facilities.map((item) => {
                      const slug = resolveCollegeAdminIconSlug(item.icon_slug);
                      const Icon =
                        getCollegeAdminErpIcon(slug) ?? LandmarkIcon;
                      return (
                        <li
                          key={item.key}
                          className="flex gap-3 py-3.5 first:pt-2"
                        >
                          <Icon
                            className="mt-0.5 size-[18px] shrink-0 text-[#9ca3af]"
                            aria-hidden
                          />
                          <div className="min-w-0">
                            <p className="text-[13px] font-medium text-[#111827]">
                              {item.title}
                            </p>
                            <p className="text-[12px] text-[#6b7280]">
                              {item.description}
                            </p>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </Panel>

                <Panel
                  title="Open campus issues"
                  actionHref={data.operations_href}
                  actionLabel="Operations →"
                >
                  {data.open_issues.length ? (
                    <ul className="divide-y divide-[#f1f5f9]">
                      {data.open_issues.map((issue) => (
                        <li
                          key={issue.issue_id}
                          className="flex flex-col gap-2 py-3.5 first:pt-2 sm:flex-row sm:items-start sm:justify-between"
                        >
                          <div className="min-w-0">
                            <p className="text-[13px] font-medium text-[#111827]">
                              {issue.title}
                            </p>
                            <p className="text-[12px] text-[#9ca3af]">
                              {issue.raised_label}
                            </p>
                          </div>
                          <IssueBadge issue={issue} />
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="py-4 text-sm text-[#9ca3af]">
                      No open maintenance issues.
                    </p>
                  )}
                </Panel>
              </div>
            </div>

            <footer className="flex flex-col gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
              <p>{data.footer_disclaimer}</p>
              <p className="tabular-nums">
                {data.footer_snapshot_label} · {formatSnapshot(data.generated_at)}
              </p>
            </footer>
          </>
        ) : null}
      </QueryState>

      {addOpen ? (
        <section
          id="add-campus"
          className="rounded-xl border border-[#dbeafe] bg-[#f8fafc] p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]"
        >
          <h3 className="text-[14px] font-semibold text-[#111827]">Add campus</h3>
          <p className="mt-1 text-[12px] text-[#6b7280]">
            Register a new campus with a unique code and official name.
          </p>
          <div className="mt-4 grid max-w-md gap-4">
            <div className="grid gap-2">
              <Label htmlFor={codeId}>Campus code</Label>
              <Input
                id={codeId}
                value={campusCode}
                onChange={(e) => setCampusCode(e.target.value)}
                placeholder="e.g. MAIN"
                autoComplete="off"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor={nameId}>Campus name</Label>
              <Input
                id={nameId}
                value={campusName}
                onChange={(e) => setCampusName(e.target.value)}
                placeholder="Official campus name"
              />
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setAddOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              className="bg-[#245dd8] hover:bg-[#1f4fb8]"
              disabled={
                create.isPending || !campusCode.trim() || !campusName.trim()
              }
              onClick={submitCreate}
            >
              {create.isPending ? "Creating…" : "Create campus"}
            </Button>
          </div>
        </section>
      ) : null}
    </div>
  );
}