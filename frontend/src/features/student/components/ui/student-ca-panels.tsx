"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function StudentCaPanel({
  title,
  children,
  actionHref,
  actionLabel,
  className,
}: {
  title: string;
  children: ReactNode;
  actionHref?: string;
  actionLabel?: string;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "overflow-hidden rounded-lg border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]",
        className,
      )}
    >
      <div className="flex items-center justify-between gap-2 border-b border-[#f1f5f9] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
        {actionHref && actionLabel ? (
          <Link href={actionHref} className="text-[12px] font-medium text-[#245dd8] hover:underline">
            {actionLabel}
          </Link>
        ) : null}
      </div>
      <div className="px-5 py-1">{children}</div>
    </section>
  );
}

export function StudentCaField({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="min-w-0 border-b border-[#f1f5f9] py-3 last:border-0 sm:py-3.5">
      <p className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">{label}</p>
      <div className="mt-1 text-[13px] font-medium text-[#111827]">{value ?? "—"}</div>
    </div>
  );
}

export function StudentPageToolbar({
  title,
  description,
  children,
}: {
  title: string;
  description?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <div className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div className="min-w-0">
        <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{title}</h2>
        {description ? (
          <p className="mt-1 max-w-2xl text-[14px] leading-relaxed text-[#6b7280]">{description}</p>
        ) : null}
      </div>
      {children ? <div className="flex shrink-0 flex-wrap gap-2">{children}</div> : null}
    </div>
  );
}

export function StudentStatusPill({
  label,
  tone = "muted",
}: {
  label: string;
  tone?: "success" | "warning" | "info" | "muted";
}) {
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
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium",
        styles[tone],
      )}
    >
      <span className={cn("size-1.5 rounded-full", dot[tone])} />
      {label}
    </span>
  );
}