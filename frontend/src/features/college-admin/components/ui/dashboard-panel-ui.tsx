"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import type { ErpIconName } from "@/components/icons/erp/names";
import { erpIconRegistry } from "@/components/icons/erp/registry";
import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { LayoutGridIcon } from "@/components/icons/erp/generated/layout-grid";
import { resolveCollegeAdminKpiIconSlug } from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { cn } from "@/lib/utils";

function ErpIcon({
  slug,
  className,
}: {
  slug: ErpIconName;
  className?: string;
}) {
  const Icon = erpIconRegistry[slug] ?? LayoutGridIcon;
  return <Icon className={className} aria-hidden strokeWidth={1.75} />;
}

export type DashboardListBadgeTone =
  | "primary"
  | "warning"
  | "success"
  | "muted"
  | "info";

export type CollegeAdminDashboardListItem = {
  id?: string;
  title: string;
  meta?: string;
  badge?: string;
  badgeTone?: DashboardListBadgeTone;
  iconSlug?: ErpIconName;
  href?: string;
  featured?: boolean;
};

export function CollegeAdminDashboardStatusBadge({
  label,
  tone = "info",
}: {
  label: string;
  tone?: DashboardListBadgeTone;
}) {
  const styles: Record<DashboardListBadgeTone, string> = {
    primary:
      "border border-transparent bg-[#245dd8] text-white shadow-[0_1px_2px_rgba(36,93,216,0.35)]",
    warning:
      "border border-[#fed7aa] bg-[#fff7ed] text-[#c2410c]",
    success:
      "border border-[#a7f3d0] bg-[#ecfdf5] text-[#047857]",
    muted:
      "border border-[#e2e8f0] bg-white text-[#64748b]",
    info:
      "border border-[#c7dafc] bg-[#f8fbff] text-[#245dd8]",
  };
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center rounded-full px-2.5 py-1 text-[11px] font-semibold leading-none tracking-tight",
        styles[tone],
      )}
    >
      {label}
    </span>
  );
}

function resolveBadgeTone(
  label: string,
  explicit?: DashboardListBadgeTone,
): DashboardListBadgeTone {
  if (explicit) return explicit;
  const normalized = label.toLowerCase();
  if (normalized.includes("up next") || normalized.includes("active")) return "primary";
  if (normalized.includes("not started")) return "muted";
  if (normalized.includes("pending") || normalized.includes("due")) return "warning";
  if (normalized.includes("complete") || normalized.includes("done")) return "success";
  return "info";
}

function DashboardListIconTile({ slug }: { slug: ErpIconName }) {
  return (
    <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-[#eff6ff]">
      <ErpIcon slug={slug} className="size-[18px] text-[#245dd8]" />
    </div>
  );
}

function DashboardListRowChevron() {
  return (
    <ChevronRightIcon
      className="size-4 shrink-0 text-[#cbd5e1]"
      aria-hidden
    />
  );
}

type DashboardListRowProps = {
  slug: ErpIconName;
  title: string;
  meta?: string;
  badge?: string;
  badgeTone?: DashboardListBadgeTone;
  href?: string;
  featured?: boolean;
  className?: string;
};

function DashboardListRow({
  slug,
  title,
  meta,
  badge,
  badgeTone,
  href,
  featured = false,
  className,
}: DashboardListRowProps) {
  const tone = badge ? resolveBadgeTone(badge, badgeTone) : undefined;
  const subtitle =
    meta && meta.trim() !== "" && meta.trim() !== title.trim() ? meta : undefined;

  const rowClass = cn(
    "grid w-full grid-cols-[2.25rem_minmax(0,1fr)_auto] items-center gap-x-3 py-3.5 text-left transition-colors",
    featured
      ? "rounded-xl border border-[#dbeafe] bg-[#f8fbff] px-3.5 shadow-[0_1px_2px_rgba(36,93,216,0.06)]"
      : "bg-white px-4 hover:bg-[#fafafa] sm:px-5",
    className,
  );

  const content = (
    <>
      <DashboardListIconTile slug={slug} />
      <div className="min-w-0">
        <p className="line-clamp-1 text-[14px] font-semibold leading-5 text-[#111827]">
          {title}
        </p>
        {subtitle ? (
          <p className="line-clamp-1 text-[12px] leading-5 text-[#6b7280]">
            {subtitle}
          </p>
        ) : null}
      </div>
      <div className="flex shrink-0 items-center gap-2 pl-1">
        {badge ? (
          <CollegeAdminDashboardStatusBadge label={badge} tone={tone ?? "muted"} />
        ) : null}
        <DashboardListRowChevron />
      </div>
    </>
  );

  if (href) {
    return (
      <Link href={href} className={rowClass}>
        {content}
      </Link>
    );
  }

  return <div className={rowClass}>{content}</div>;
}

export function CollegeAdminDashboardPanel({
  title,
  children,
  actionHref,
  actionLabel = "View all",
  className,
  description,
  bodyClassName,
  /** List-style body (full-bleed rows); default adds chart/content padding */
  flushBody = false,
}: {
  title: string;
  children: ReactNode;
  actionHref?: string;
  actionLabel?: string;
  className?: string;
  description?: string;
  bodyClassName?: string;
  flushBody?: boolean;
}) {
  return (
    <section
      className={cn(
        "rounded-2xl border border-[#e5e7eb] bg-white shadow-[0_1px_3px_rgba(15,23,42,0.06)]",
        className,
      )}
    >
      <div className="flex items-center justify-between gap-3 border-b border-[#eef2f7] px-5 py-3.5">
        <div className="min-w-0">
          <h3 className="text-[15px] font-bold tracking-[-0.02em] text-[#0f2744]">
            {title}
          </h3>
          {description ? (
            <p className="mt-0.5 text-[12px] leading-snug text-[#64748b]">
              {description}
            </p>
          ) : null}
        </div>
        {actionHref ? (
          <Link
            href={actionHref}
            className="group inline-flex shrink-0 items-center gap-1 rounded-lg px-2 py-1 text-[12px] font-semibold text-[#245dd8] transition-colors hover:bg-[#eef4ff]"
          >
            <span>{actionLabel.replace(/\s*→\s*$/, "")}</span>
            <ChevronRightIcon className="size-3.5 transition-transform group-hover:translate-x-0.5" />
          </Link>
        ) : null}
      </div>
      <div
        className={cn(
          "min-h-0 bg-white",
          flushBody ? "py-1" : "px-5 pb-5 pt-4",
          bodyClassName,
        )}
      >
        {children}
      </div>
    </section>
  );
}

/** Compact row-style empty state (matches premium task list — no dashed hero block). */
export function CollegeAdminDashboardEmptyState({
  message,
  iconSlug = "inbox",
  title = "Nothing to show yet",
  badgeLabel = "Not started",
}: {
  message: string;
  iconSlug?: ErpIconName;
  title?: string;
  badgeLabel?: string;
}) {
  return (
    <ul>
      <li className="px-2 py-2">
        <DashboardListRow
          slug={iconSlug}
          title={title}
          meta={message}
          badge={badgeLabel}
          badgeTone="muted"
          featured
        />
      </li>
    </ul>
  );
}

export function CollegeAdminDashboardSideList({
  items,
  empty,
  emptyIconSlug,
  emptyTitle,
  emptyBadgeLabel = "Not started",
  highlightFirst = true,
}: {
  items: CollegeAdminDashboardListItem[];
  empty: string;
  emptyIconSlug?: ErpIconName;
  emptyTitle?: string;
  emptyBadgeLabel?: string;
  /** First row uses featured highlight (reference: “Up next” row). */
  highlightFirst?: boolean;
}) {
  if (!items.length) {
    return (
      <CollegeAdminDashboardEmptyState
        message={empty}
        iconSlug={emptyIconSlug ?? "inbox"}
        title={emptyTitle ?? "All caught up"}
        badgeLabel={emptyBadgeLabel}
      />
    );
  }

  return (
    <ul>
      {items.map((item, index) => {
        const slug =
          item.iconSlug ??
          resolveCollegeAdminKpiIconSlug(item.title, item.meta ?? item.title);
        const featured = item.featured ?? (highlightFirst && index === 0);
        const key = item.id ?? `${item.title}-${index}`;

        return (
          <li
            key={key}
            className={cn(
              "border-b border-[#f1f5f9] last:border-b-0",
              featured && "px-2 py-2",
            )}
          >
            <DashboardListRow
              slug={slug}
              title={item.title}
              meta={item.meta}
              badge={item.badge}
              badgeTone={item.badgeTone}
              href={item.href}
              featured={featured}
            />
          </li>
        );
      })}
    </ul>
  );
}

/** @deprecated Use CollegeAdminDashboardPanel — kept as `Panel` for gradual migration */
export const Panel = CollegeAdminDashboardPanel;

/** Shared shell for table / list / sidebar panels across college-admin dashboards. */
export const collegeAdminPanelShellClass =
  "overflow-hidden rounded-2xl border border-[#e5e7eb] bg-white shadow-[0_1px_3px_rgba(15,23,42,0.06)]";

export function CollegeAdminPanelShell({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <section className={cn(collegeAdminPanelShellClass, className)}>{children}</section>;
}

export function CollegeAdminPanelChromeHeader({
  title,
  description,
  trailing,
}: {
  title: string;
  description?: string;
  trailing?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3 border-b border-[#eef2f7] bg-white px-5 py-4">
      <div className="min-w-0">
        <h3 className="text-[15px] font-bold tracking-[-0.02em] text-[#0f2744]">{title}</h3>
        {description ? (
          <p className="mt-0.5 text-[12px] leading-snug text-[#64748b]">{description}</p>
        ) : null}
      </div>
      {trailing ? <div className="flex shrink-0 items-center gap-2">{trailing}</div> : null}
    </div>
  );
}

export function CollegeAdminPanelChromeFooter({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-center justify-between gap-2 border-t border-[#eef2f7] bg-[#fafbfc] px-5 py-3.5 text-[12px] font-medium text-[#64748b]",
        className,
      )}
    >
      {children}
    </div>
  );
}

/** Centered empty block for main table/list panels (calendar, semesters, years, etc.). */
export function CollegeAdminPanelEmptyState({
  iconSlug = "inbox",
  title = "Nothing here yet",
  description,
  action,
  className,
}: {
  iconSlug?: ErpIconName;
  title?: string;
  description: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex min-h-[min(22rem,50vh)] flex-col items-center justify-center px-6 py-10 text-center sm:px-10",
        className,
      )}
    >
      <div className="flex size-[3.25rem] items-center justify-center rounded-2xl border border-[#dbeafe] bg-gradient-to-br from-[#eff6ff] via-[#f5f9ff] to-white shadow-[0_4px_16px_rgba(36,93,216,0.1)]">
        <ErpIcon slug={iconSlug} className="size-7 text-[#245dd8]" />
      </div>
      <h4 className="mt-5 text-[15px] font-semibold tracking-[-0.01em] text-[#111827]">{title}</h4>
      <p className="mt-2 max-w-[26rem] text-[13px] leading-relaxed text-[#6b7280]">{description}</p>
      {action ? <div className="mt-6 flex flex-wrap items-center justify-center gap-2">{action}</div> : null}
    </div>
  );
}

/** Primary content card: title bar, body (table or empty), optional footer strip. */
export function CollegeAdminTablePanel({
  title,
  description,
  footer,
  children,
  className,
  bodyClassName,
}: {
  title: string;
  description?: string;
  footer?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <CollegeAdminPanelShell className={cn("flex min-h-0 flex-col", className)}>
      <CollegeAdminPanelChromeHeader title={title} description={description} />
      <div className={cn("min-h-0 flex-1 bg-white", bodyClassName)}>{children}</div>
      {footer ? <CollegeAdminPanelChromeFooter>{footer}</CollegeAdminPanelChromeFooter> : null}
    </CollegeAdminPanelShell>
  );
}

/** Sidebar / ancillary panel with padded body. */
export function CollegeAdminSidePanel({
  title,
  description,
  children,
  className,
  footer,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
  footer?: ReactNode;
}) {
  return (
    <CollegeAdminPanelShell className={className}>
      <CollegeAdminPanelChromeHeader title={title} description={description} />
      <div className="px-5 py-4">{children}</div>
      {footer ? <CollegeAdminPanelChromeFooter>{footer}</CollegeAdminPanelChromeFooter> : null}
    </CollegeAdminPanelShell>
  );
}