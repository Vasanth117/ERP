"use client";

import type { ReactNode } from "react";

import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import { cn } from "@/lib/utils";

/** Figma ST 02 panel card — border #dce3ec, 8px radius, 14px semibold title. */
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
    <section
      className={cn(
        "overflow-hidden rounded-lg border border-[#dce3ec] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]",
        className,
      )}
    >
      <div className="border-b border-[#dce3ec] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#172b45]">{title}</h3>
      </div>
      <div>{children}</div>
      {footer ? (
        <div className="border-t border-[#dce3ec] px-5 py-3 text-[12px] font-medium text-[#607086]">{footer}</div>
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
      <span className="text-[11px] font-normal text-[#607086]">{label}</span>
      <span className="text-[13px] font-medium text-[#172b45]">{value}</span>
    </div>
  );
}

export function StAcademicsPageBlock({
  title,
  description,
  figmaNode,
  actions,
  children,
}: {
  title: string;
  description: string;
  figmaNode: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="space-y-5" data-figma-frame={figmaNode}>
      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-[26px] font-semibold tracking-tight text-[#172b45]">{title}</h2>
          <p className="mt-1.5 text-[13px] text-[#607086]">{description}</p>
        </div>
        {actions ? <div className="shrink-0">{actions}</div> : null}
      </header>
      {children}
    </section>
  );
}

const OUTCOME_STYLES: Record<string, { wrap: string; dot: string; text: string }> = {
  success: { wrap: "bg-[#e7f6ed]", dot: "bg-[#1f7a45]", text: "text-[#1f7a45]" },
  info: { wrap: "bg-[#ebf2ff]", dot: "bg-[#245dd8]", text: "text-[#245dd8]" },
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
    <div className="flex gap-3 border-t border-[#dce3ec] px-5 py-4 first:border-t-0">
      <CollegeAdminIcon name={icon === "map-pin" ? "map-pin" : "phone"} size={18} className="mt-0.5 text-[#607086]" />
      <div>
        <p className="text-[13px] font-medium text-[#172b45]">{label}</p>
        <p className="mt-0.5 text-[12px] text-[#607086]">{value}</p>
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
        checked ? "bg-[#245dd8]" : "bg-[#dce3ec]",
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