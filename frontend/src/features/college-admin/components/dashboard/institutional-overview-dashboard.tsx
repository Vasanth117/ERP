"use client";

import Link from "next/link";
import { useCallback, type ReactNode } from "react";

import { CollegeAdminDashboardPanel as Panel } from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { Button } from "@/components/ui/button";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { CollegeAdminKpiGrid } from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState, StatCard } from "@/features/college-admin/components/ui/query-state";
import { useInstitutionalOverview } from "@/features/college-admin/hooks/use-institution";
import type { ComplianceStatusItem } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function StatusPill({
  label,
  tone,
}: {
  label: string;
  tone: "success" | "warning" | "info" | "muted";
}) {
  const styles = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium",
        styles[tone],
      )}
    >
      <span
        className={cn(
          "size-1.5 rounded-full",
          tone === "success" && "bg-[#10b981]",
          tone === "warning" && "bg-[#f97316]",
          tone === "info" && "bg-[#3b82f6]",
          tone === "muted" && "bg-[#9ca3af]",
        )}
      />
      {label}
    </span>
  );
}

function complianceTone(code: string): "success" | "warning" | "info" | "muted" {
  if (code === "valid" || code === "approved") return "success";
  if (code === "due_soon" || code === "pending") return "warning";
  if (code === "upcoming") return "info";
  return "muted";
}

function complianceLabel(item: ComplianceStatusItem): string {
  const map: Record<string, string> = {
    valid: "Valid",
    approved: "Approved",
    pending: "Pending",
    due_soon: "Due soon",
    upcoming: "Upcoming",
  };
  return map[item.status_code] ?? item.status_code;
}

function ProfileField({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-b border-[#f1f5f9] py-3 last:border-0 sm:py-3.5">
      <p className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
        {label}
      </p>
      <p className="mt-1 text-[13px] font-medium text-[#111827]">{value || "—"}</p>
    </div>
  );
}

export function InstitutionalOverviewDashboard() {
  const { data, isLoading, isError, error, refetch } = useInstitutionalOverview();

  const handleDownload = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `institution-overview-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const profile = data?.profile;
  const stats = data?.statistics;
  const displayName = profile?.display_name ?? profile?.legal_name ?? "Institution";
  const programmeTotal =
    data?.programme_mix.reduce((sum, row) => sum + row.student_count, 0) ?? 0;

  const campusSummary =
    data && data.campuses.length
      ? data.campuses
          .slice(0, 2)
          .map((c) => c.name)
          .join(" · ")
      : "No campuses yet";

  return (
    <div className="space-y-5" data-figma-frame="65:185">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            Institutional overview
          </h2>
          <p className="mt-1 max-w-2xl text-[14px] leading-relaxed text-[#6b7280]">
            Profile, campuses, programmes and accreditation status for{" "}
            <span className="font-medium text-[#374151]">{displayName}</span>
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            href="/college-admin/institution/profile"
            className="inline-flex h-9 items-center rounded-md border border-[#e5e7eb] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            Edit profile
          </Link>
          <Button
            type="button"
            className="h-9 gap-1.5 border border-[#245dd8] bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8]"
            onClick={handleDownload}
            disabled={isLoading || !data}
          >
            <CollegeAdminDownload className="size-3.5" />
            Download profile
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
            <CollegeAdminKpiGrid>
              <StatCard
                label="Campuses"
                value={data.campuses.length}
                hint={campusSummary}
                kpiKey="campuses"
                index={0}
                iconSlug="landmark"
              />
              <StatCard
                label="Departments"
                value={stats?.department_count ?? 0}
                hint={`${stats?.programme_count ?? 0} active programmes`}
                kpiKey="departments"
                index={1}
                iconSlug="building-2"
              />
              <StatCard
                label="Programmes"
                value={stats?.programme_count ?? 0}
                hint={`${stats?.total_students ?? 0} enrolled students`}
                kpiKey="programmes"
                index={2}
                iconSlug="book-open"
              />
              <StatCard
                label="Accreditation"
                value={data.accreditation_summary ?? "Not configured"}
                hint={data.accreditation_detail ?? "Set affiliation in institution profile"}
                kpiKey="accreditation"
                index={3}
                iconSlug="award"
              />
            </CollegeAdminKpiGrid>

            <div className="grid gap-4 xl:grid-cols-3">
              <div className="space-y-4 xl:col-span-2">
                <Panel
                  title="Institution profile"
                  actionHref="/college-admin/institution/settings"
                  actionLabel="Institution settings →"
                >
                  <div className="grid gap-x-8 sm:grid-cols-2">
                    <ProfileField label="Institution name" value={profile?.legal_name ?? ""} />
                    <ProfileField
                      label="Institution code"
                      value={profile?.institution_code ?? profile?.tenant_code ?? "—"}
                    />
                    <ProfileField
                      label="Type"
                      value={
                        [profile?.institution_type, profile?.affiliation_type]
                          .filter(Boolean)
                          .join(" · ") || "—"
                      }
                    />
                    <ProfileField
                      label="Affiliating university"
                      value={profile?.affiliation_name ?? "—"}
                    />
                    <ProfileField label="Contact email" value={profile?.institution_email ?? "—"} />
                    <ProfileField label="Contact phone" value={profile?.contact_phone ?? "—"} />
                    <ProfileField label="Official website" value={profile?.official_website ?? "—"} />
                    <ProfileField
                      label="Locale · timezone"
                      value={`${profile?.locale ?? "—"} · ${profile?.timezone ?? "—"}`}
                    />
                  </div>
                </Panel>

                <Panel
                  title="Campuses"
                  actionHref="/college-admin/institution/campuses"
                  actionLabel="Manage campuses →"
                >
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[520px] text-left text-[13px]">
                      <thead>
                        <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          <th className="pb-2 pr-3 font-medium">Campus</th>
                          <th className="pb-2 pr-3 font-medium">Location</th>
                          <th className="pb-2 pr-3 font-medium">Students</th>
                          <th className="pb-2 pr-3 font-medium">Departments</th>
                          <th className="pb-2 font-medium">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.campuses.map((campus) => (
                          <tr key={campus.campus_id} className="border-b border-[#f8fafc]">
                            <td className="py-2.5 pr-3 font-medium text-[#111827]">
                              <Link
                                href={`/college-admin/institution/campuses/${campus.campus_id}`}
                                className="hover:text-[#245dd8] hover:underline"
                              >
                                {campus.name}
                                {campus.is_main ? (
                                  <span className="ml-1.5 text-[11px] font-normal text-[#6b7280]">
                                    (main)
                                  </span>
                                ) : null}
                              </Link>
                            </td>
                            <td className="py-2.5 pr-3 text-[#6b7280]">{campus.location_label}</td>
                            <td className="py-2.5 pr-3 tabular-nums text-[#6b7280]">
                              {campus.student_count}
                            </td>
                            <td className="py-2.5 pr-3 tabular-nums text-[#6b7280]">
                              {campus.department_count}
                            </td>
                            <td className="py-2.5">
                              <StatusPill
                                label={campus.is_active ? "Active" : "Inactive"}
                                tone={campus.is_active ? "success" : "muted"}
                              />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-[12px] text-[#6b7280]">
                    <span>
                      {data.campuses.length} campus{data.campuses.length === 1 ? "" : "es"}
                    </span>
                    <Link
                      href="/college-admin/institution/campuses"
                      className="font-medium text-[#245dd8] hover:underline"
                    >
                      View campus details →
                    </Link>
                  </div>
                </Panel>

                <Panel
                  title="Programme mix by level"
                  actionHref="/college-admin/academics/academic-configuration-dashboard"
                  actionLabel="Academic configuration →"
                >
                  {data.programme_mix.length ? (
                    <ul className="space-y-4">
                      {data.programme_mix.map((row) => {
                        const pct =
                          programmeTotal > 0
                            ? Math.round((row.student_count / programmeTotal) * 100)
                            : 0;
                        return (
                          <li key={row.level}>
                            <div className="mb-1.5 flex items-center justify-between gap-2 text-[13px]">
                              <span className="font-medium text-[#111827]">{row.label}</span>
                              <span className="tabular-nums text-[#6b7280]">
                                {row.student_count.toLocaleString("en-IN")} students ·{" "}
                                {row.programme_count} programmes
                              </span>
                            </div>
                            <div className="h-2 overflow-hidden rounded-full bg-[#eef2f7]">
                              <div
                                className="h-full rounded-full bg-[#245dd8]"
                                style={{ width: `${Math.max(pct, row.student_count ? 2 : 0)}%` }}
                              />
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">
                      No programme enrollment data yet. Configure programmes in Academics.
                    </p>
                  )}
                </Panel>
              </div>

              <div className="space-y-4">
                <Panel
                  title="Accreditation & compliance"
                  actionHref="/college-admin/institution/policies"
                  actionLabel="View documents →"
                >
                  <ul className="space-y-3 text-[13px]">
                    {data.compliance_items.map((item) => (
                      <li key={item.title} className="flex items-center justify-between gap-2">
                        <span className="text-[#374151]">{item.title}</span>
                        <StatusPill
                          label={complianceLabel(item)}
                          tone={complianceTone(item.status_code)}
                        />
                      </li>
                    ))}
                  </ul>
                </Panel>

                <Panel
                  title="Key contacts"
                  actionHref="/college-admin/users/user-management-dashboard"
                  actionLabel="Directory →"
                >
                  {data.key_contacts.length ? (
                    <ul className="space-y-3 text-sm">
                      {data.key_contacts.map((contact) => (
                        <li key={`${contact.name}-${contact.role_label}`}>
                          <p className="font-medium text-[#111827]">{contact.name}</p>
                          <p className="text-[12px] text-[#6b7280]">{contact.role_label}</p>
                          {contact.email ? (
                            <a
                              href={`mailto:${contact.email}`}
                              className="mt-0.5 block text-[12px] text-[#245dd8] hover:underline"
                            >
                              {contact.email}
                            </a>
                          ) : null}
                          {contact.phone ? (
                            <p className="text-[12px] text-[#9ca3af]">{contact.phone}</p>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">
                      No directory contacts yet. Assign department heads or faculty designations.
                    </p>
                  )}
                </Panel>
              </div>
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}