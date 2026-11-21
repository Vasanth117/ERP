"use client";

import type { ReactNode } from "react";

import type { ErpIconName } from "@/components/icons/erp/names";
import { erpIconRegistry } from "@/components/icons/erp/registry";
import { LayoutGridIcon } from "@/components/icons/erp/generated/layout-grid";
import { cn } from "@/lib/utils";

export type CollegeAdminKpiTone = "blue" | "purple" | "green" | "amber";

export const COLLEGE_ADMIN_KPI_TONES: CollegeAdminKpiTone[] = ["blue", "purple", "green", "amber"];

const TONE_STYLES: Record<
  CollegeAdminKpiTone,
  {
    surface: string;
    icon: string;
    iconRing: string;
    hint: string;
    watermark: string;
  }
> = {
  blue: {
    surface:
      "border-[#bfdbfe]/90 bg-gradient-to-br from-[#eff6ff] via-[#f5f9ff] to-[#fafcff] shadow-[0_1px_2px_rgba(37,99,235,0.06)]",
    icon: "text-[#2563eb]",
    iconRing: "shadow-[0_4px_14px_rgba(37,99,235,0.14)]",
    hint: "text-[#3b82f6]",
    watermark: "text-[#93c5fd]",
  },
  purple: {
    surface:
      "border-[#ddd6fe]/90 bg-gradient-to-br from-[#f5f3ff] via-[#faf8ff] to-[#fdfcff] shadow-[0_1px_2px_rgba(124,58,237,0.06)]",
    icon: "text-[#7c3aed]",
    iconRing: "shadow-[0_4px_14px_rgba(124,58,237,0.14)]",
    hint: "text-[#8b5cf6]",
    watermark: "text-[#c4b5fd]",
  },
  green: {
    surface:
      "border-[#bbf7d0]/90 bg-gradient-to-br from-[#ecfdf5] via-[#f4fdf8] to-[#fafffc] shadow-[0_1px_2px_rgba(16,185,129,0.06)]",
    icon: "text-[#059669]",
    iconRing: "shadow-[0_4px_14px_rgba(16,185,129,0.14)]",
    hint: "text-[#10b981]",
    watermark: "text-[#6ee7b7]",
  },
  amber: {
    surface:
      "border-[#fde68a]/90 bg-gradient-to-br from-[#fffbeb] via-[#fffdf5] to-[#fffffa] shadow-[0_1px_2px_rgba(245,158,11,0.06)]",
    icon: "text-[#d97706]",
    iconRing: "shadow-[0_4px_14px_rgba(245,158,11,0.14)]",
    hint: "text-[#f59e0b]",
    watermark: "text-[#fcd34d]",
  },
};

export function collegeAdminKpiToneForIndex(index: number): CollegeAdminKpiTone {
  return COLLEGE_ADMIN_KPI_TONES[Math.abs(index) % COLLEGE_ADMIN_KPI_TONES.length]!;
}

export function collegeAdminKpiToneForKey(key: string): CollegeAdminKpiTone {
  let hash = 0;
  for (let i = 0; i < key.length; i += 1) {
    hash = (hash + key.charCodeAt(i) * (i + 3)) % 997;
  }
  return collegeAdminKpiToneForIndex(hash);
}

const KPI_KEY_ICON: Array<{ test: (key: string, label: string) => boolean; icon: ErpIconName }> = [
  { test: (k, l) => k.includes("upload") || l.includes("upload"), icon: "upload" },
  { test: (k, l) => k.includes("import") || l.includes("import"), icon: "download" },
  { test: (k, l) => k.includes("calendar") || l.includes("calendar"), icon: "calendar-days" },
  { test: (k, l) => k.includes("semester") || l.includes("semester"), icon: "calendar-range" },
  { test: (k, l) => k.includes("programme") || l.includes("program"), icon: "book-open" },
  { test: (k, l) => k.includes("curriculum") || l.includes("curriculum"), icon: "library-big" },
  { test: (k, l) => k.includes("course") || l.includes("course"), icon: "notebook-text" },
  { test: (k, l) => k.includes("student") || l.includes("student"), icon: "graduation-cap" },
  { test: (k, l) => k.includes("faculty") || l.includes("faculty"), icon: "users-round" },
  { test: (k, l) => k.includes("teacher") || l.includes("teacher"), icon: "user-round-cog" },
  { test: (k, l) => k.includes("user") || l.includes("user"), icon: "users" },
  { test: (k, l) => k.includes("role") || l.includes("role"), icon: "shield-check" },
  { test: (k, l) => k.includes("login") || l.includes("login"), icon: "log-in" },
  { test: (k, l) => k.includes("active") || l.includes("active"), icon: "user-check" },
  { test: (k, l) => k.includes("pending") || l.includes("pending") || l.includes("awaiting"), icon: "clock" },
  { test: (k, l) => k.includes("approv"), icon: "square-check" },
  { test: (k, l) => k.includes("alert") || l.includes("warning") || l.includes("attention"), icon: "triangle-alert" },
  { test: (k, l) => k.includes("critical") || l.includes("critical"), icon: "circle-alert" },
  { test: (k, l) => k.includes("finance") || l.includes("fee") || l.includes("revenue"), icon: "wallet" },
  { test: (k, l) => k.includes("attendance") || l.includes("attendance"), icon: "clipboard-check" },
  { test: (k, l) => k.includes("exam") || l.includes("exam"), icon: "file-text" },
  { test: (k, l) => k.includes("department") || l.includes("department"), icon: "building-2" },
  { test: (k, l) => k.includes("campus") || l.includes("campus"), icon: "landmark" },
  { test: (k, l) => k.includes("resource") || l.includes("lab"), icon: "flask-conical" },
  { test: (k, l) => k.includes("category") || l.includes("categor"), icon: "folder" },
  { test: (k, l) => k.includes("ticket") || l.includes("ticket"), icon: "life-buoy" },
  { test: (k, l) => k.includes("report") || l.includes("report"), icon: "chart-bar" },
  { test: (k, l) => k.includes("config") || l.includes("setup"), icon: "settings-2" },
  { test: (k, l) => k.includes("complete") || l.includes("done") || l.includes("imported"), icon: "circle-check-big" },
  { test: (k, l) => k.includes("progress") || l.includes("progress"), icon: "loader-circle" },
  { test: (k, l) => k.includes("total"), icon: "layers" },
];

export function resolveCollegeAdminKpiIconSlug(key: string, label: string): ErpIconName {
  const k = key.toLowerCase();
  const l = label.toLowerCase();
  for (const rule of KPI_KEY_ICON) {
    if (rule.test(k, l)) return rule.icon;
  }
  return "layout-grid";
}

function ErpKpiIcon({ slug, className }: { slug: ErpIconName; className?: string }) {
  const Icon = erpIconRegistry[slug] ?? LayoutGridIcon;
  return <Icon className={className} aria-hidden />;
}

function hintToneClass(tone?: string): string | undefined {
  if (tone === "success") return "text-[#059669]";
  if (tone === "warning") return "text-[#d97706]";
  if (tone === "error" || tone === "danger") return "text-[#dc2626]";
  if (tone === "info") return "text-[#2563eb]";
  return undefined;
}

function valueToneClass(tone?: string): string {
  if (tone === "danger" || tone === "error") return "text-[#dc2626]";
  if (tone === "success") return "text-[#047857]";
  if (tone === "warning") return "text-[#d97706]";
  return "text-[#111827]";
}

export type CollegeAdminKpiCardProps = {
  label: string;
  value: string | number;
  hint?: ReactNode;
  hintTone?: string;
  valueTone?: string;
  iconSlug?: ErpIconName;
  tone?: CollegeAdminKpiTone;
  index?: number;
  kpiKey?: string;
  className?: string;
};

export function CollegeAdminKpiCard({
  label,
  value,
  hint,
  hintTone,
  valueTone,
  iconSlug,
  tone,
  index = 0,
  kpiKey,
  className,
}: CollegeAdminKpiCardProps) {
  const cardTone = tone ?? (kpiKey ? collegeAdminKpiToneForKey(kpiKey) : collegeAdminKpiToneForIndex(index));
  const styles = TONE_STYLES[cardTone];
  const slug = iconSlug ?? resolveCollegeAdminKpiIconSlug(kpiKey ?? label, label);
  const hintClass = hintToneClass(hintTone) ?? styles.hint;
  const resolvedValueTone =
    valueTone ?? (hintTone === "danger" || hintTone === "error" ? hintTone : undefined);

  return (
    <article
      className={cn(
        "relative flex min-h-[8.75rem] flex-col justify-between overflow-hidden rounded-2xl border p-4 transition-[transform,box-shadow] duration-200 hover:-translate-y-px hover:shadow-[0_8px_24px_rgba(15,23,42,0.08)]",
        styles.surface,
        className,
      )}
    >
      <div
        className="pointer-events-none absolute -bottom-3 -right-3 opacity-[0.22]"
        aria-hidden
      >
        <ErpKpiIcon slug={slug} className={cn("size-[5.5rem]", styles.watermark)} />
      </div>

      <div className="relative z-[1] flex items-start gap-3">
        <div
          className={cn(
            "flex size-10 shrink-0 items-center justify-center rounded-xl border border-white/80 bg-white",
            styles.iconRing,
          )}
        >
          <ErpKpiIcon slug={slug} className={cn("size-[1.125rem]", styles.icon)} />
        </div>
        <div className="min-w-0 flex-1 pt-0.5">
          <p className="text-[13px] font-semibold leading-snug text-[#374151]">{label}</p>
          <p
            className={cn(
              "mt-1 text-[1.625rem] font-bold leading-none tracking-tight tabular-nums",
              valueToneClass(resolvedValueTone),
            )}
          >
            {value}
          </p>
        </div>
      </div>

      {hint ? (
        <p className={cn("relative z-[1] mt-3 text-[12px] leading-snug", hintClass)}>{hint}</p>
      ) : (
        <span className="relative z-[1] mt-3 block min-h-[1.125rem]" aria-hidden />
      )}
    </article>
  );
}

/** @deprecated Use {@link CollegeAdminKpiCard} — kept as alias for gradual migration. */
export function StatCard({
  label,
  value,
  hint,
  index,
  iconSlug,
  tone,
  kpiKey,
}: {
  label: string;
  value: string | number;
  hint?: string;
  index?: number;
  iconSlug?: ErpIconName;
  tone?: CollegeAdminKpiTone;
  kpiKey?: string;
}) {
  return (
    <CollegeAdminKpiCard
      label={label}
      value={value}
      hint={hint}
      index={index}
      iconSlug={iconSlug}
      tone={tone}
      kpiKey={kpiKey ?? label}
    />
  );
}

export function CollegeAdminKpiGrid({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={cn("grid gap-4 sm:grid-cols-2 xl:grid-cols-4", className)}>{children}</div>;
}

export function CollegeAdminUserDashboardKpiCard({
  kpi,
  index,
}: {
  kpi: {
    key: string;
    label: string;
    value: string;
    hint_line: string;
    hint_tone: string;
  };
  index: number;
}) {
  return (
    <CollegeAdminKpiCard
      kpiKey={kpi.key}
      label={kpi.label}
      value={kpi.value}
      hint={kpi.hint_line}
      hintTone={kpi.hint_tone}
      index={index}
    />
  );
}

export function CollegeAdminDashboardKpiCard({
  label,
  value,
  hint,
  hintTone,
  valueTone,
  kpiKey,
  index,
  iconSlug,
  tone,
}: {
  label: string;
  value: string | number;
  hint?: ReactNode;
  hintTone?: string;
  valueTone?: string;
  kpiKey?: string;
  index?: number;
  iconSlug?: ErpIconName;
  tone?: CollegeAdminKpiTone;
}) {
  return (
    <CollegeAdminKpiCard
      label={label}
      value={value}
      hint={hint}
      hintTone={hintTone}
      valueTone={valueTone}
      kpiKey={kpiKey ?? label}
      index={index}
      iconSlug={iconSlug}
      tone={tone}
    />
  );
}