"use client";

import type { ReactNode } from "react";

import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import {
  PORTAL_CARD,
  PORTAL_PAGE_DESC,
  STUDENT_TAB_PAGE_TITLE,
  PORTAL_SURFACE_BORDER,
  STUDENT_TEXT_MUTED,
  STUDENT_TEXT_PRIMARY,
} from "@/features/student/components/ui/student-portal-tokens";
import { cn } from "@/lib/utils";

/** Figma ST 02 panel card — matches student portal shell tokens. */
export function StAcademicsSectionCard({
  title,
  children,
  footer,
  className,
}: {
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn(PORTAL_CARD, className)}>
      <div className={cn("border-b px-5 py-3.5", PORTAL_SURFACE_BORDER)}>
        <h3 className={cn("text-[14px] font-semibold", STUDENT_TEXT_PRIMARY)}>{title}</h3>
      </div>
      <div>{children}</div>
      {footer ? (
        <div className={cn("border-t px-5 py-3 text-[12px] font-medium", PORTAL_SURFACE_BORDER, STUDENT_TEXT_MUTED)}>
          {footer}
        </div>
      ) : null}
    </section>
  );
}

export function StAcademicsDetailRow({
  fields,
}: {
  fields: { label: string; value: string }[];
}) {
  return (
    <div
      className={cn(
        "grid gap-4 py-2.5",
        fields.length > 1 ? "grid-cols-1 sm:grid-cols-2" : "grid-cols-1",
      )}
    >
      {fields.map((field) => (
        <StAcademicsDetailField key={field.label} label={field.label} value={field.value} />
      ))}
    </div>
  );
}

export function StAcademicsDetailField({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex min-w-0 flex-col gap-1">
      <span className={cn("text-[11px] font-normal", STUDENT_TEXT_MUTED)}>{label}</span>
      <span className={cn("text-[13px] font-medium", STUDENT_TEXT_PRIMARY)}>{value}</span>
    </div>
  );
}

export function StAcademicsPageBlock({
  title,
  description,
  figmaNode,
  actions,
  belowDescription,
  children,
  compact,
}: {
  title: string;
  description: string;
  figmaNode: string;
  actions?: ReactNode;
  /** Row under title + subtitle (e.g. back navigation). */
  belowDescription?: ReactNode;
  children: ReactNode;
  compact?: boolean;
}) {
  return (
    <section className={cn(compact ? "space-y-3" : "space-y-5")} data-figma-frame={figmaNode}>
      <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-2">
          <h2 className={STUDENT_TAB_PAGE_TITLE}>{title}</h2>
          <p className={PORTAL_PAGE_DESC}>{description}</p>
          {belowDescription ? <div className="pt-0.5">{belowDescription}</div> : null}
        </div>
        {actions ? <div className="shrink-0">{actions}</div> : null}
      </header>
      {children}
    </section>
  );
}

const OUTCOME_STYLES: Record<string, { wrap: string; dot: string; text: string }> = {
  success: { wrap: "bg-[#e7f6ed]", dot: "bg-[#1f7a45]", text: "text-[#1f7a45]" },
  info: { wrap: "bg-[#ebf2ff]", dot: "bg-[#2563eb]", text: "text-[#2563eb]" },
  warning: { wrap: "bg-[#fff7ed]", dot: "bg-[#c2410c]", text: "text-[#c2410c]" },
  muted: { wrap: "bg-[#eef1f5]", dot: "bg-[#6b7280]", text: "text-[#6b7280]" },
};

export function StAcademicsOutcomeBadge({ label, tone }: { label: string; tone: string }) {
  const style = OUTCOME_STYLES[tone] ?? OUTCOME_STYLES.muted!;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded px-1.5 py-0.5 text-[11px] font-semibold",
        style.wrap,
        style.text,
      )}
    >
      <span className={cn("size-[5px] rounded-full", style.dot)} aria-hidden />
      {label}
    </span>
  );
}

export function StAcademicsResultBadge({ label }: { label: string }) {
  const passed = label.toLowerCase() === "passed";
  return (
    <StAcademicsOutcomeBadge label={label} tone={passed ? "success" : "muted"} />
  );
}

export function StDepartmentContactRow({
  icon,
  label,
  value,
}: {
  icon: "map-pin" | "phone";
  label: string;
  value: string;
}) {
  return (
    <div className={cn("flex gap-3 border-t px-5 py-4 first:border-t-0", PORTAL_SURFACE_BORDER)}>
      <CollegeAdminIcon name={icon === "map-pin" ? "map-pin" : "phone"} size={18} className={cn("mt-0.5", STUDENT_TEXT_MUTED)} />
      <div>
        <p className={cn("text-[13px] font-medium", STUDENT_TEXT_PRIMARY)}>{label}</p>
        <p className={cn("mt-0.5 text-[12px]", STUDENT_TEXT_MUTED)}>{value}</p>
      </div>
    </div>
  );
}

/** ST 02.09 — declaration toggle (32×18 pill, Figma 164:6683). */
export function StAcademicsToggle({
  checked,
  onChange,
  disabled,
  ariaLabel,
}: {
  checked: boolean;
  onChange: (next: boolean) => void;
  disabled?: boolean;
  ariaLabel: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={ariaLabel}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative h-[18px] w-8 shrink-0 rounded-full transition-colors duration-200",
        checked ? "bg-[#2563eb]" : "bg-[#dce3ec]",
        disabled && "cursor-not-allowed opacity-50",
      )}
    >
      <span
        className={cn(
          "absolute top-[2px] left-[2px] size-[14px] rounded-full bg-white shadow-[0_1px_2px_rgba(15,23,42,0.12)] transition-transform duration-200",
          checked && "translate-x-[14px]",
        )}
      />
    </button>
  );
}

export function displayOrDash(value: string | number | null | undefined): string {
  if (value == null) return "—";
  const text = String(value).trim();
  return text || "—";
}