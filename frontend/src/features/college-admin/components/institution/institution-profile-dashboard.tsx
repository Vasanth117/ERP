"use client";

import Link from "next/link";
import { useCallback, type ReactNode } from "react";

import { GlobeIcon } from "@/components/icons/erp/generated/globe";
import { LandmarkIcon } from "@/components/icons/erp/generated/landmark";
import { MailIcon } from "@/components/icons/erp/generated/mail";
import { MapPinIcon } from "@/components/icons/erp/generated/map-pin";
import { PencilIcon } from "@/components/icons/erp/generated/pencil";
import { PhoneIcon } from "@/components/icons/erp/generated/phone";
import { UserRoundIcon } from "@/components/icons/erp/generated/user-round";
import { Button } from "@/components/ui/button";
import {
  CollegeAdminDownload,
  getCollegeAdminErpIcon,
  resolveCollegeAdminIconSlug,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useInstitutionProfilePage } from "@/features/college-admin/hooks/use-institution";
import type {
  InstitutionStatusBadge,
  ProfileCompletenessRow,
} from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

const COMPLETENESS_BAR_COLORS: Record<string, string> = {
  basic_information: "bg-[#7dd3fc]",
  branding_assets: "bg-[#245dd8]",
  campus_details: "bg-[#34d399]",
  policies_uploaded: "bg-[#d4a574]",
};

function StatusBadge({ badge }: { badge: InstitutionStatusBadge }) {
  const styles = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    info: "bg-[#3b82f6]",
    muted: "bg-[#9ca3af]",
  };
  const tone = badge.tone in styles ? badge.tone : "muted";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium",
        styles[tone as keyof typeof styles],
      )}
    >
      <span className={cn("size-1.5 rounded-full", dot[tone as keyof typeof dot])} />
      {badge.label}
    </span>
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

function AboutDetail({
  label,
  value,
}: {
  label: string;
  value: string | null;
}) {
  return (
    <div className="min-w-0 py-3">
      <p className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
        {label}
      </p>
      <p className="mt-1 text-[13px] font-medium text-[#111827]">{value || "—"}</p>
    </div>
  );
}

function CompletenessRow({ row }: { row: ProfileCompletenessRow }) {
  const barColor = COMPLETENESS_BAR_COLORS[row.key] ?? "bg-[#245dd8]";
  return (
    <div className="py-3">
      <div className="mb-2 flex items-center justify-between gap-2 text-[13px]">
        <span className="text-[#374151]">{row.label}</span>
        <span className="font-medium text-[#111827]">{row.status_label}</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#e5e7eb]">
        <div
          className={cn("h-full rounded-full transition-all", barColor)}
          style={{ width: `${Math.min(100, Math.max(0, row.progress_percent))}%` }}
        />
      </div>
    </div>
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

export function InstitutionProfileDashboard() {
  const { data, isLoading, isError, error, refetch } = useInstitutionProfilePage();

  const handleDownload = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `institution-profile-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const profile = data?.profile;
  const accent = data?.branding_primary_color ?? "#245dd8";

  return (
    <div className="space-y-5" data-figma-frame="72:5933">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            Institution Profile
          </h2>
          <p className="mt-1 max-w-2xl text-[14px] leading-relaxed text-[#6b7280]">
            Official identity, affiliation and leadership of the institution
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] bg-white text-xs font-medium text-[#374151]"
            onClick={handleDownload}
            disabled={isLoading || !data}
          >
            <CollegeAdminDownload className="size-3.5" />
            Download profile
          </Button>
          <Link
            href="/college-admin/institution/information"
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <PencilIcon className="size-3.5" aria-hidden />
            Edit information
          </Link>
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
            <section className="rounded-xl border border-[#e8ecf2] bg-white p-6 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
                <div
                  className="flex size-16 shrink-0 items-center justify-center rounded-xl text-white"
                  style={{ backgroundColor: accent }}
                >
                  <LandmarkIcon className="size-8" aria-hidden />
                </div>
                <div className="min-w-0 flex-1 space-y-2.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-[18px] font-bold text-[#111827]">
                      {data.display_name}
                    </h3>
                    {data.status_badges.map((badge) => (
                      <StatusBadge key={badge.label} badge={badge} />
                    ))}
                  </div>
                  {data.subtitle_line ? (
                    <p className="text-[13px] text-[#6b7280]">{data.subtitle_line}</p>
                  ) : null}
                  <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-[13px] text-[#4b5563]">
                    {data.location_label ? (
                      <span className="inline-flex items-center gap-1.5">
                        <MapPinIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                        {data.location_label}
                      </span>
                    ) : null}
                    {profile?.official_website ? (
                      <span className="inline-flex items-center gap-1.5">
                        <GlobeIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                        {profile.official_website.replace(/^https?:\/\//, "")}
                      </span>
                    ) : null}
                    {profile?.institution_email ? (
                      <span className="inline-flex items-center gap-1.5">
                        <MailIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                        {profile.institution_email}
                      </span>
                    ) : null}
                    {profile?.contact_phone ? (
                      <span className="inline-flex items-center gap-1.5">
                        <PhoneIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                        {profile.contact_phone}
                      </span>
                    ) : null}
                  </div>
                </div>
              </div>
            </section>

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_392px]">
              <div className="space-y-5">
                <Panel
                  title="About the institution"
                  actionHref="/college-admin/institution/information"
                  actionLabel="Edit →"
                >
                  <div className="grid gap-x-8 sm:grid-cols-2">
                    {data.about_fields.map((field) => (
                      <AboutDetail
                        key={field.label}
                        label={field.label}
                        value={field.value}
                      />
                    ))}
                  </div>
                </Panel>

                <Panel
                  title="Leadership"
                  actionHref="/college-admin/organization/department-management-dashboard"
                  actionLabel="Manage roles →"
                >
                  {data.leadership.length ? (
                    <ul className="divide-y divide-[#f1f5f9]">
                      {data.leadership.map((row) => (
                        <li
                          key={`${row.name}-${row.role_label}`}
                          className="flex gap-3 py-3.5 first:pt-2"
                        >
                          <UserRoundIcon
                            className="mt-0.5 size-[18px] shrink-0 text-[#9ca3af]"
                            aria-hidden
                          />
                          <div className="min-w-0">
                            <p className="text-[13px] font-medium text-[#111827]">
                              {row.name}
                            </p>
                            <p className="text-[12px] text-[#6b7280]">
                              {row.detail_line ?? row.role_label}
                            </p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="py-4 text-sm text-[#9ca3af]">
                      No leadership contacts on file yet.
                    </p>
                  )}
                </Panel>
              </div>

              <div className="space-y-5">
                <Panel
                  title="Profile completeness"
                  actionHref="/college-admin/institution/information"
                  actionLabel="Complete profile →"
                >
                  {data.profile_completeness.map((row) => (
                    <CompletenessRow key={row.key} row={row} />
                  ))}
                </Panel>

                <Panel title="Related settings">
                  <ul className="divide-y divide-[#f1f5f9]">
                    {data.related_settings.map((item) => {
                      const slug =
                        item.key === "branding"
                          ? "landmark"
                          : item.key === "campuses"
                            ? "map-pin"
                            : "calendar-check";
                      const Icon =
                        getCollegeAdminErpIcon(resolveCollegeAdminIconSlug(slug)) ??
                        LandmarkIcon;
                      return (
                        <li
                          key={item.key}
                          className="flex items-start gap-3 py-3.5 first:pt-2"
                        >
                          <Icon
                            className="mt-0.5 size-[18px] shrink-0 text-[#9ca3af]"
                            aria-hidden
                          />
                          <div className="min-w-0 flex-1">
                            <p className="text-[13px] font-medium text-[#111827]">
                              {item.title}
                            </p>
                            <p className="text-[12px] text-[#6b7280]">{item.description}</p>
                          </div>
                          <Link
                            href={item.href}
                            className="shrink-0 text-[12px] font-medium text-[#245dd8] hover:underline"
                          >
                            Open →
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                </Panel>
              </div>
            </div>

            <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af]">
              <span>{data.footer_disclaimer}</span>
              <span>Snapshot · {formatSnapshot(data.generated_at)}</span>
            </footer>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}