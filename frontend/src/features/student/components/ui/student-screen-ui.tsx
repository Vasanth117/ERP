"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { PORTAL_PAGE_DESC, PORTAL_PAGE_TITLE } from "@/lib/portal/shell-styles";
import { cn } from "@/lib/utils";

export { QueryState, StatCard, CollegeAdminKpiGrid } from "@/features/college-admin/components/ui/query-state";
export { CollegeAdminDashboardKpiCard } from "@/features/college-admin/components/ui/college-admin-kpi-card";

export function SectionPanel({
  title,
  children,
  actionHref,
  actionLabel,
  className,
  variant = "default",
}: {
  title: string;
  children: ReactNode;
  actionHref?: string;
  actionLabel?: string;
  className?: string;
  variant?: "default" | "subtle";
}) {
  return (
    <section
      className={cn(
        "rounded-lg border border-[#e8ecf2] p-4 sm:p-5",
        variant === "subtle"
          ? "bg-[#fafbfc] shadow-none"
          : "bg-white shadow-[0_1px_2px_rgba(23,43,69,0.04)]",
        className,
      )}
    >
      <div className="mb-4 flex items-center justify-between gap-2">
        <h3 className="text-[15px] font-semibold tracking-[-0.01em] text-[#111827]">{title}</h3>
        {actionHref && actionLabel ? (
          <Link
            href={actionHref}
            className="shrink-0 text-[12px] font-medium text-[#245dd8] hover:underline"
          >
            {actionLabel}
          </Link>
        ) : null}
      </div>
      {children}
    </section>
  );
}

/** In-page heading — module title + tabs live in `StudentPortalChrome`. */
export function PageHeading({
  title,
  description,
  figmaPage,
}: {
  title?: string;
  description?: string;
  figmaPage?: string;
}) {
  if (!title && !description) return null;
  return (
    <div
      className="mb-5"
      data-figma-page={figmaPage}
    >
      {title ? <h2 className={PORTAL_PAGE_TITLE}>{title}</h2> : null}
      {description ? (
        <p className={cn(PORTAL_PAGE_DESC, "max-w-3xl", title && "mt-1.5")}>{description}</p>
      ) : null}
    </div>
  );
}

export function DetailRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="border-b border-[#f1f5f9] py-3 last:border-0">
      <p className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">{label}</p>
      <div className="mt-1 text-[13px] font-medium text-[#111827]">{value ?? "—"}</div>
    </div>
  );
}

export function StatusBadge({
  label,
  tone = "muted",
}: {
  label: string;
  tone?: "success" | "warning" | "danger" | "info" | "muted";
}) {
  const styles = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    danger: "bg-[#fef2f2] text-[#b91c1c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-medium capitalize",
        styles[tone],
      )}
    >
      {label.replace(/_/g, " ")}
    </span>
  );
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatTime(value: string): string {
  if (!value) return "—";
  const parts = value.split(":");
  if (parts.length < 2) return value;
  const h = Number(parts[0]);
  const m = parts[1];
  const ampm = h >= 12 ? "PM" : "AM";
  const hr = h % 12 || 12;
  return `${hr}:${m} ${ampm}`;
}

export function toneForStatus(status: string): "success" | "warning" | "danger" | "info" | "muted" {
  const s = status.toLowerCase();
  if (["active", "approved", "confirmed", "eligible", "open", "valid", "submitted"].includes(s)) {
    return "success";
  }
  if (["pending", "in_review", "due_soon", "partial"].includes(s)) return "warning";
  if (["rejected", "cancelled", "closed", "ineligible"].includes(s)) return "danger";
  if (["draft", "submitted"].includes(s)) return "info";
  return "muted";
}