"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { erpIconRegistry } from "@/components/icons/erp/registry";
import { LayoutGridIcon } from "@/components/icons/erp/generated/layout-grid";
import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import {
  type CollegeAdminKpiTone,
  collegeAdminKpiToneForIndex,
  collegeAdminKpiToneStyles,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import type { ErpIconName } from "@/components/icons/erp/names";
import type { ProfileCorrectionFieldName } from "@/features/student/lib/profile-correction-fields";
import {
  PORTAL_CARD,
  PORTAL_CARD_BODY,
  PORTAL_CARD_HEADER,
  PORTAL_MODULE_TITLE,
  PORTAL_PAGE_DESC,
} from "@/lib/portal/shell-styles";
import { cn } from "@/lib/utils";

export const profileCardClassName = PORTAL_CARD;

export const profileCardHeaderClassName = PORTAL_CARD_HEADER;

export const profileCardBodyClassName = PORTAL_CARD_BODY;

export function ProfilePageHeading({
  title,
  description,
  actions,
  backHref,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  backHref?: string;
}) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between" data-figma-node="164:625">
      <div className="flex min-w-0 items-start gap-3">
        {backHref ? (
          <Link
            href={backHref}
            className="mt-1 inline-flex size-8 items-center justify-center rounded-md border border-[#dce3ec] text-[#607086] hover:bg-[#f8fafc]"
            aria-label="Back to profile overview"
          >
            <CollegeAdminIcon name="arrow-left" size={16} />
          </Link>
        ) : null}
        <div className="min-w-0">
          <h1 className={PORTAL_MODULE_TITLE}>{title}</h1>
          {description ? (
            <p className={cn(PORTAL_PAGE_DESC, "max-w-2xl")}>{description}</p>
          ) : null}
        </div>
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

export function ProfileHeaderCard({
  initials,
  fullName,
  badges,
  metaLine,
  email,
  phone,
  batchLabel,
}: {
  initials: string;
  fullName: string;
  badges: { label: string; tone: "success" | "info" }[];
  metaLine: string;
  email: string;
  phone: string;
  batchLabel: string;
}) {
  return (
    <section
      className={cn(profileCardClassName, "px-6 py-5")}
      data-figma-node="164:636"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="flex size-16 shrink-0 items-center justify-center rounded-full bg-[#ebf2ff] text-lg font-semibold text-[#245dd8]">
          {initials}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-lg font-semibold text-[#172b45]">{fullName}</h2>
            {badges.map((b) => (
              <ProfileStatusBadge key={b.label} label={b.label} tone={b.tone} />
            ))}
          </div>
          <p className="mt-1 text-[13px] text-[#607086]">{metaLine}</p>
          <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-[12px] text-[#607086]">
            <span className="inline-flex items-center gap-1.5">
              <CollegeAdminIcon name="mail" size={14} />
              {email}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <CollegeAdminIcon name="phone" size={14} />
              {phone}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <CollegeAdminIcon name="calendar" size={14} />
              {batchLabel}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}

function ProfileStatusBadge({
  label,
  tone,
}: {
  label: string;
  tone: "success" | "info";
}) {
  const styles =
    tone === "success"
      ? "bg-[#e7f6ed] text-[#1f7a45]"
      : "bg-[#ebf2ff] text-[#245dd8]";
  const dot = tone === "success" ? "bg-[#1f7a45]" : "bg-[#245dd8]";
  return (
    <span className={cn("inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-semibold", styles)}>
      <span className={cn("size-1.5 rounded-full", dot)} aria-hidden />
      {label}
    </span>
  );
}

export function ProfilePanel({
  title,
  children,
  action,
  figmaNode,
}: {
  title: string;
  children: ReactNode;
  action?: ReactNode;
  figmaNode?: string;
}) {
  return (
    <section className={profileCardClassName} data-figma-node={figmaNode}>
      <div className={profileCardHeaderClassName}>
        <h3 className="text-[14px] font-semibold text-[#172b45]">{title}</h3>
        {action}
      </div>
      <div className={profileCardBodyClassName}>{children}</div>
    </section>
  );
}

export function ProfileDetailGrid({
  rows,
  variant = "default",
}: {
  rows: { label: string; value: string; href?: string }[][];
  /** `personal` — Figma ST 01.03 sentence-case labels and value weight */
  variant?: "default" | "personal";
}) {
  return (
    <div className="space-y-0" data-figma-node="164:670">
      {rows.map((pair, i) => (
        <div
          key={`row-${i}`}
          className="grid gap-x-12 gap-y-5 border-b border-[#eef2f6] py-[18px] last:border-0 sm:grid-cols-2"
        >
          {pair.map((field) => (
            <ProfileDetailField key={field.label} variant={variant} {...field} />
          ))}
        </div>
      ))}
    </div>
  );
}

function ProfileDetailField({
  label,
  value,
  href,
  variant = "default",
}: {
  label: string;
  value: string;
  href?: string;
  variant?: "default" | "personal";
}) {
  const labelClass =
    variant === "personal"
      ? "text-[12px] font-normal text-[#607086]"
      : "text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]";
  const valueClass =
    variant === "personal"
      ? "mt-1.5 text-[14px] font-semibold text-[#172b45]"
      : "mt-1 text-[13px] font-medium text-[#111827]";

  const body = (
    <>
      <p className={labelClass}>{label}</p>
      <p className={valueClass}>{value || "—"}</p>
    </>
  );
  if (href) {
    return (
      <Link href={href} className="block rounded-md transition-colors hover:bg-[#f8fafc] -mx-2 px-2 py-1">
        {body}
        <span className="mt-1 inline-block text-[11px] font-semibold text-[#245dd8]">View details →</span>
      </Link>
    );
  }
  return <div>{body}</div>;
}

export function ProfileRequestUpdateButton({
  className,
  defaultField,
}: {
  className?: string;
  /** Pre-selects a correction field on the update-requests form (POST body `field_name`). */
  defaultField?: ProfileCorrectionFieldName;
}) {
  const href = defaultField
    ? `/student/profile/update-requests?field=${encodeURIComponent(defaultField)}`
    : "/student/profile/update-requests";
  return (
    <Link
      href={href}
      className={cn(
        "inline-flex h-[33px] items-center gap-2 rounded-md border border-[#245dd8] bg-[#245dd8] px-3.5 text-[12px] font-semibold text-white hover:bg-[#1f4fb8]",
        className,
      )}
    >
      <CollegeAdminIcon name="pencil" size={15} className="text-white" />
      Request update
    </Link>
  );
}

export function ProfileEditDetailsButton({
  className,
  hash,
}: {
  className?: string;
  /** Optional hash on the edit screen (e.g. contact fields). */
  hash?: string;
}) {
  const href = hash ? `/student/profile/edit#${hash}` : "/student/profile/edit";
  return (
    <Link
      href={href}
      className={cn(
        "inline-flex h-[33px] items-center gap-2 rounded-md border border-[#245dd8] bg-[#245dd8] px-3.5 text-[12px] font-semibold text-white hover:bg-[#1f4fb8]",
        className,
      )}
    >
      <CollegeAdminIcon name="pencil" size={15} className="text-white" />
      Edit details
    </Link>
  );
}

export function ProfileAcademicOverviewButton({ className }: { className?: string }) {
  return (
    <Link
      href="/student/academics"
      className={cn(
        "inline-flex h-[33px] items-center gap-2 rounded-md border border-[#245dd8] bg-[#245dd8] px-3.5 text-[12px] font-semibold text-white hover:bg-[#1f4fb8]",
        className,
      )}
    >
      <CollegeAdminIcon name="chevron-right" size={15} className="text-white" />
      Academic overview
    </Link>
  );
}

export function ProfileAdvisorPanel({
  classAdvisorName,
  mentorName,
}: {
  classAdvisorName?: string | null;
  mentorName?: string | null;
}) {
  return (
    <ProfilePanel title="Advisor" figmaNode="164:1305">
      <ProfileAdvisorRow label="Class advisor" name={classAdvisorName} />
      <ProfileAdvisorRow label="Mentor" name={mentorName} bordered={false} />
    </ProfilePanel>
  );
}

function ProfileAdvisorRow({
  label,
  name,
  bordered = true,
}: {
  label: string;
  name?: string | null;
  bordered?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 py-3",
        bordered && "border-b border-[#eef2f6]",
      )}
    >
      <CollegeAdminIcon name="user-round" size={18} className="shrink-0 text-[#607086]" />
      <span className="min-w-0 flex-1">
        <span className="block text-[13px] font-medium text-[#172b45]">{label}</span>
        <span className="mt-0.5 block text-[11px] text-[#607086]">{name?.trim() || "—"}</span>
      </span>
    </div>
  );
}

export function ProfileVerificationPanel({
  identityVerified,
  lastUpdated,
}: {
  identityVerified: boolean;
  lastUpdated: string;
}) {
  const statusLabel = identityVerified ? "Verified" : "Pending review";

  return (
    <ProfilePanel title="Verification" figmaNode="164:780">
      <ul className="space-y-0">
        <li className="flex items-start justify-between gap-3 pb-4">
          <span className="flex items-start gap-2.5">
            <CollegeAdminIcon name="circle-check" size={18} className="mt-0.5 shrink-0 text-[#607086]" />
            <span>
              <span className="block text-[13px] font-medium text-[#172b45]">Identity documents</span>
              <span className="mt-0.5 block text-[12px] text-[#607086]">{statusLabel}</span>
            </span>
          </span>
          <ProfileStatusBadge label={statusLabel} tone={identityVerified ? "success" : "info"} />
        </li>
        <li className="flex items-start gap-2.5 border-t border-[#eef2f6] pt-4">
          <CollegeAdminIcon name="clock" size={18} className="mt-0.5 shrink-0 text-[#607086]" />
          <span>
            <span className="block text-[12px] text-[#607086]">Last updated</span>
            <span className="mt-1 block text-[14px] font-semibold text-[#172b45]">{lastUpdated}</span>
          </span>
        </li>
      </ul>
    </ProfilePanel>
  );
}

export function ProfilePreferenceRow({
  icon,
  label,
  enabled,
}: {
  icon: ErpIconName;
  label: string;
  enabled: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-[#eef1f5] py-3.5 last:border-0">
      <span className="flex min-w-0 flex-1 items-center gap-2 text-[13px] text-[#172b45]">
        <CollegeAdminIcon name={icon} size={16} className="shrink-0 text-[#607086]" />
        <span>
          <span className="block font-medium">{label}</span>
          <span className="text-[11px] text-[#607086]">{enabled ? "Enabled" : "Disabled"}</span>
        </span>
      </span>
      <ProfileStatusBadge label={enabled ? "On" : "Off"} tone={enabled ? "success" : "info"} />
    </div>
  );
}

export function ProfileGuardianCard({
  title,
  rows,
}: {
  title: string;
  rows: { label: string; value: string }[];
}) {
  return (
    <ProfilePanel title={title}>
      <div className="grid gap-6 sm:grid-cols-2">
        {rows.map((field) => (
          <div key={field.label}>
            <p className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">{field.label}</p>
            <p className="mt-1 text-[13px] font-medium text-[#111827]">{field.value || "—"}</p>
          </div>
        ))}
      </div>
    </ProfilePanel>
  );
}

export function ProfileEmergencyHighlight({
  name,
  relationship,
  phone,
}: {
  name: string;
  relationship: string;
  phone: string;
}) {
  return (
    <ProfilePanel title="Emergency contact">
      <div className="flex items-center gap-3">
        <span className="inline-flex size-10 items-center justify-center rounded-md bg-[#ebf2ff] text-[#245dd8]">
          <CollegeAdminIcon name="phone" size={18} />
        </span>
        <div>
          <p className="text-[14px] font-semibold text-[#172b45]">{name}</p>
          <p className="mt-0.5 text-[12px] text-[#607086]">
            {relationship} · {phone}
          </p>
        </div>
      </div>
    </ProfilePanel>
  );
}

export type ProfileExploreLink = {
  title: string;
  description?: string;
  href: string;
  icon: ErpIconName;
  figmaNode?: string;
  tone?: CollegeAdminKpiTone;
};

export function ProfileQuickLinkList({ links }: { links: ProfileExploreLink[] }) {
  return (
    <ul className="divide-y divide-[#eef1f5]" data-figma-node="164:697">
      {links.map((link) => (
        <li key={link.href}>
          <Link
            href={link.href}
            className="flex items-center gap-3 py-3 text-[13px] font-medium text-[#172b45] transition-colors hover:text-[#245dd8]"
          >
            <CollegeAdminIcon name={link.icon} size={18} className="text-[#607086]" />
            <span className="min-w-0 flex-1">
              {link.title}
              {link.description ? (
                <span className="mt-0.5 block text-[11px] font-normal text-[#607086]">
                  {link.description}
                </span>
              ) : null}
            </span>
            <CollegeAdminIcon name="chevron-right" size={14} className="text-[#8a98aa]" />
          </Link>
        </li>
      ))}
    </ul>
  );
}

function ExploreCardIcon({ slug, className }: { slug: ErpIconName; className?: string }) {
  const Icon = erpIconRegistry[slug] ?? LayoutGridIcon;
  return <Icon className={className} aria-hidden strokeWidth={1.75} />;
}

/** Gradient navigation cards (ST 01.02) — links to ST 01.03–01.06. */
export function ProfileExploreCardGrid({ cards }: { cards: ProfileExploreLink[] }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card, index) => {
        const cardTone = card.tone ?? collegeAdminKpiToneForIndex(index);
        const styles = collegeAdminKpiToneStyles(cardTone);
        return (
          <Link
            key={card.href}
            href={card.href}
            data-figma-node={card.figmaNode}
            className={cn(
              "group relative flex min-h-[10.5rem] flex-col justify-between overflow-hidden rounded-[18px] border p-[18px] shadow-[0_2px_8px_rgba(15,23,42,0.04)] transition-[transform,box-shadow] duration-200 hover:-translate-y-0.5 hover:shadow-[0_12px_28px_rgba(15,23,42,0.1)]",
              styles.surface,
            )}
          >
            <div
              className={cn(
                "pointer-events-none absolute -left-8 -top-8 size-28 rounded-full opacity-25 blur-2xl",
                styles.glow,
              )}
              aria-hidden
            />
            <div className="pointer-events-none absolute -bottom-5 -right-4 opacity-[0.18]" aria-hidden>
              <ExploreCardIcon slug={card.icon} className={cn("size-[5.5rem]", styles.watermark)} />
            </div>

            <div className="relative z-[1]">
              <div
                className={cn(
                  "mb-4 inline-flex size-11 items-center justify-center rounded-[14px] border border-white/90 bg-white ring-1",
                  styles.iconTile,
                )}
              >
                <ExploreCardIcon slug={card.icon} className={cn("size-5", styles.icon)} />
              </div>
              <p className="text-[14px] font-semibold leading-snug text-[#0f172a] group-hover:text-[#172b45]">
                {card.title}
              </p>
              {card.description ? (
                <p className="mt-1.5 text-[12px] leading-relaxed text-[#475569]">{card.description}</p>
              ) : null}
            </div>

            <p className={cn("relative z-[1] mt-4 text-[12px] font-semibold", styles.hint)}>Open →</p>
          </Link>
        );
      })}
    </div>
  );
}

export function ProfileInfoBanner({
  title,
  description,
  actionHref,
  actionLabel,
}: {
  title: string;
  description: string;
  actionHref: string;
  actionLabel: string;
}) {
  return (
    <div className="flex flex-col gap-3 rounded-md border border-[#93c5fd] bg-[#ebf2ff] p-4 sm:flex-row sm:items-center">
      <CollegeAdminIcon name="info" size={18} className="shrink-0 text-[#245dd8]" />
      <div className="min-w-0 flex-1">
        <p className="text-[12px] font-semibold text-[#172b45]">{title}</p>
        <p className="mt-1 text-[11px] text-[#607086]">{description}</p>
      </div>
      <Link href={actionHref} className="shrink-0 text-[11px] font-semibold text-[#245dd8] hover:underline">
        {actionLabel}
      </Link>
    </div>
  );
}

/** Figma ST 01.07 — pill switch (not square checkbox). */
export function ProfileFieldSwitch({
  label,
  description,
  checked,
  onChange,
  disabled,
  layout = "stacked",
}: {
  label: string;
  description?: string;
  checked: boolean;
  onChange: (next: boolean) => void;
  disabled?: boolean;
  /** `stacked` — label above switch (field inclusion grid); `inline` — label left, switch right */
  layout?: "stacked" | "inline";
}) {
  const switchControl = (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative h-6 w-11 shrink-0 rounded-full transition-colors duration-200",
        checked ? "bg-[#245dd8]" : "bg-[#dce3ec]",
        disabled && "cursor-not-allowed opacity-50",
      )}
    >
      <span
        className={cn(
          "absolute top-0.5 left-0.5 size-5 rounded-full bg-white shadow-[0_1px_2px_rgba(15,23,42,0.12)] transition-transform duration-200",
          checked && "translate-x-5",
        )}
      />
    </button>
  );

  if (layout === "inline") {
    return (
      <div className="flex items-center justify-between gap-3 border-b border-[#eef2f6] py-3 last:border-0">
        <span className="min-w-0">
          <span className="block text-[13px] font-medium text-[#172b45]">{label}</span>
          {description ? (
            <span className="mt-0.5 block text-[11px] text-[#607086]">{description}</span>
          ) : null}
        </span>
        {switchControl}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <span className="text-[12px] font-normal text-[#607086]">{label}</span>
      {description ? <span className="-mt-1 text-[11px] text-[#8a98aa]">{description}</span> : null}
      {switchControl}
    </div>
  );
}

/** @deprecated Use ProfileFieldSwitch — kept for call sites migrating to stacked layout */
export function ProfileToggleRow(props: Parameters<typeof ProfileFieldSwitch>[0]) {
  return <ProfileFieldSwitch {...props} layout={props.layout ?? "inline"} />;
}

export function ProfileFormField({
  label,
  children,
  className,
}: {
  label: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <label className={cn("block", className)}>
      <span className="mb-1.5 block text-[12px] font-normal text-[#607086]">{label}</span>
      {children}
    </label>
  );
}

export function profileInitials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase();
  return `${parts[0]![0] ?? ""}${parts[parts.length - 1]![0] ?? ""}`.toUpperCase();
}

export function formatStandingLabel(value: string | null | undefined): string {
  if (!value) return "—";
  return value.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}