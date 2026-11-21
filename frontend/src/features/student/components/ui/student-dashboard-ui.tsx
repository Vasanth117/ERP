"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import type { ErpIconName } from "@/components/icons/erp/names";
import { cn } from "@/lib/utils";

/** Figma ST 01.01 — flat KPI card (node 164:254). */
export function StDashboardKpiCard({
  label,
  value,
  hint,
  hintTone = "muted",
}: {
  label: string;
  value: string;
  hint: string;
  hintTone?: "success" | "info" | "muted" | "warning";
}) {
  const hintClass = {
    success: "text-[#1f7a45]",
    info: "text-[#245dd8]",
    muted: "text-[#607086]",
    warning: "text-[#946009]",
  }[hintTone];

  return (
    <article className="flex min-w-0 flex-1 flex-col gap-2 rounded-lg border border-[#dce3ec] bg-white p-5">
      <p className="text-[12px] text-[#607086]">{label}</p>
      <p className="text-[26px] font-semibold leading-none text-[#172b45]">{value}</p>
      <p className={cn("text-[11px]", hintClass)}>{hint}</p>
    </article>
  );
}

export function StDashboardKpiRow({ children }: { children: ReactNode }) {
  return (
    <div
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
      data-figma-node="164:253"
    >
      {children}
    </div>
  );
}

export function StDashboardPanel({
  title,
  action,
  children,
  footer,
}: {
  title: string;
  action?: { href: string; label: string };
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-lg border border-[#dce3ec] bg-white">
      <div className="flex items-center justify-between gap-3 border-b border-[#dce3ec] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#172b45]">{title}</h3>
        {action ? (
          <Link
            href={action.href}
            className="shrink-0 text-[11px] font-semibold text-[#245dd8] hover:underline"
          >
            {action.label}
          </Link>
        ) : null}
      </div>
      <div>{children}</div>
      {footer ? (
        <div className="border-t border-[#dce3ec] px-5 py-3 text-[11px] text-[#607086]">{footer}</div>
      ) : null}
    </section>
  );
}

export function StNoticeBanner({
  title,
  description,
  href,
  linkLabel = "View shortage →",
}: {
  title: string;
  description: string;
  href: string;
  linkLabel?: string;
}) {
  return (
    <div
      className="flex w-full items-center gap-3 rounded-md bg-[#fff5df] p-4"
      data-figma-node="164:270"
    >
      <CollegeAdminIcon name="triangle-alert" size={18} className="shrink-0 text-[#946009]" />
      <div className="min-w-0 flex-1">
        <p className="text-[12px] font-semibold text-[#172b45]">{title}</p>
        <p className="mt-1 text-[11px] text-[#607086]">{description}</p>
      </div>
      <Link href={href} className="shrink-0 text-[11px] font-semibold text-[#245dd8] hover:underline">
        {linkLabel}
      </Link>
    </div>
  );
}

export type StNotificationBadgeTone = "alert" | "exam" | "due" | "fees" | "info";

export function StNotificationBadge({
  label,
  tone,
}: {
  label: string;
  tone: StNotificationBadgeTone;
}) {
  const styles: Record<StNotificationBadgeTone, string> = {
    alert: "bg-[#fdecec] text-[#c03535]",
    exam: "bg-[#ebf2ff] text-[#245dd8]",
    due: "bg-[#fff5df] text-[#946009]",
    fees: "bg-[#e7f6ed] text-[#1f7a45]",
    info: "bg-[#eef1f5] text-[#607086]",
  };
  const dot: Record<StNotificationBadgeTone, string> = {
    alert: "bg-[#c03535]",
    exam: "bg-[#245dd8]",
    due: "bg-[#946009]",
    fees: "bg-[#1f7a45]",
    info: "bg-[#607086]",
  };
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-semibold",
        styles[tone],
      )}
    >
      <span className={cn("size-1.5 rounded-full", dot[tone])} aria-hidden />
      {label}
    </span>
  );
}

export function StNotificationRow({
  icon,
  title,
  meta,
  badgeLabel,
  badgeTone,
}: {
  icon: ErpIconName;
  title: string;
  meta: string;
  badgeLabel: string;
  badgeTone: StNotificationBadgeTone;
}) {
  return (
    <li className="flex items-center gap-3 border-b border-[#f1f5f9] py-3 last:border-0">
      <CollegeAdminIcon name={icon} size={18} className="shrink-0 text-[#607086]" />
      <div className="min-w-0 flex-1">
        <p className="text-[13px] font-medium text-[#172b45]">{title}</p>
        <p className="text-[11px] text-[#607086]">{meta}</p>
      </div>
      <StNotificationBadge label={badgeLabel} tone={badgeTone} />
    </li>
  );
}

export function StSecondaryButton({
  href,
  icon,
  label,
}: {
  href: string;
  icon: ErpIconName;
  label: string;
}) {
  return (
    <Link
      href={href}
      className="inline-flex h-[35px] items-center gap-2 rounded-md border border-[#dce3ec] bg-white px-3.5 text-[12px] font-semibold text-[#172b45] hover:bg-[#f8fafc]"
    >
      <CollegeAdminIcon name={icon} size={15} />
      {label}
    </Link>
  );
}

export function StPrimaryButton({
  href,
  icon,
  label,
}: {
  href: string;
  icon: ErpIconName;
  label: string;
}) {
  return (
    <Link
      href={href}
      className="inline-flex h-[33px] items-center gap-2 rounded-md bg-[#245dd8] px-3.5 text-[12px] font-semibold text-white hover:bg-[#1f4fb8]"
    >
      <CollegeAdminIcon name={icon} size={15} className="text-white" />
      {label}
    </Link>
  );
}