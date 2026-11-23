"use client";

import {
  Children,
  cloneElement,
  isValidElement,
  type ReactElement,
  type ReactNode,
} from "react";

import type { ErpIconName } from "@/components/icons/erp/names";
import { erpIconRegistry } from "@/components/icons/erp/registry";
import { LayoutGridIcon } from "@/components/icons/erp/generated/layout-grid";
import { cn } from "@/lib/utils";

export type CollegeAdminKpiTone =
  | "blue"
  | "purple"
  | "green"
  | "amber"
  | "rose"
  | "cyan"
  | "indigo"
  | "teal";

export const COLLEGE_ADMIN_KPI_TONES: CollegeAdminKpiTone[] = [
  "blue",
  "purple",
  "green",
  "amber",
  "rose",
  "cyan",
  "indigo",
  "teal",
];

const TONE_STYLES: Record<
  CollegeAdminKpiTone,
  {
    surface: string;
    glow: string;
    icon: string;
    iconTile: string;
    hint: string;
    watermark: string;
  }
> = {
  blue: {
    surface: "border-[#93c5fd]/55 bg-gradient-to-br from-[#dbeafe] via-[#e8f2ff] to-[#f8fbff]",
    glow: "bg-[#3b82f6]",
    icon: "text-[#1d4ed8]",
    iconTile: "shadow-[0_8px_20px_rgba(37,99,235,0.22)] ring-[#bfdbfe]/80",
    hint: "text-[#2563eb]",
    watermark: "text-[#60a5fa]",
  },
  purple: {
    surface: "border-[#c4b5fd]/55 bg-gradient-to-br from-[#ede9fe] via-[#f3efff] to-[#faf8ff]",
    glow: "bg-[#8b5cf6]",
    icon: "text-[#6d28d9]",
    iconTile: "shadow-[0_8px_20px_rgba(124,58,237,0.2)] ring-[#ddd6fe]/80",
    hint: "text-[#7c3aed]",
    watermark: "text-[#a78bfa]",
  },
  green: {
    surface: "border-[#6ee7b7]/55 bg-gradient-to-br from-[#d1fae5] via-[#e8fdf3] to-[#f6fffa]",
    glow: "bg-[#10b981]",
    icon: "text-[#047857]",
    iconTile: "shadow-[0_8px_20px_rgba(16,185,129,0.2)] ring-[#a7f3d0]/80",
    hint: "text-[#059669]",
    watermark: "text-[#34d399]",
  },
  amber: {
    surface: "border-[#fcd34d]/55 bg-gradient-to-br from-[#fef3c7] via-[#fff8e6] to-[#fffdf5]",
    glow: "bg-[#f59e0b]",
    icon: "text-[#b45309]",
    iconTile: "shadow-[0_8px_20px_rgba(245,158,11,0.22)] ring-[#fde68a]/80",
    hint: "text-[#d97706]",
    watermark: "text-[#fbbf24]",
  },
  rose: {
    surface: "border-[#fda4af]/55 bg-gradient-to-br from-[#ffe4e6] via-[#fff1f2] to-[#fffafb]",
    glow: "bg-[#f43f5e]",
    icon: "text-[#be123c]",
    iconTile: "shadow-[0_8px_20px_rgba(244,63,94,0.2)] ring-[#fecdd3]/80",
    hint: "text-[#e11d48]",
    watermark: "text-[#fb7185]",
  },
  cyan: {
    surface: "border-[#67e8f9]/55 bg-gradient-to-br from-[#cffafe] via-[#e6fffe] to-[#f4ffff]",
    glow: "bg-[#06b6d4]",
    icon: "text-[#0e7490]",
    iconTile: "shadow-[0_8px_20px_rgba(6,182,212,0.22)] ring-[#a5f3fc]/80",
    hint: "text-[#0891b2]",
    watermark: "text-[#22d3ee]",
  },
  indigo: {
    surface: "border-[#a5b4fc]/55 bg-gradient-to-br from-[#e0e7ff] via-[#eef2ff] to-[#f8f9ff]",
    glow: "bg-[#6366f1]",
    icon: "text-[#4338ca]",
    iconTile: "shadow-[0_8px_20px_rgba(99,102,241,0.22)] ring-[#c7d2fe]/80",
    hint: "text-[#4f46e5]",
    watermark: "text-[#818cf8]",
  },
  teal: {
    surface: "border-[#5eead4]/55 bg-gradient-to-br from-[#ccfbf1] via-[#e6faf5] to-[#f4fffc]",
    glow: "bg-[#14b8a6]",
    icon: "text-[#0f766e]",
    iconTile: "shadow-[0_8px_20px_rgba(20,184,166,0.22)] ring-[#99f6e4]/80",
    hint: "text-[#0d9488]",
    watermark: "text-[#2dd4bf]",
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

export function resolveCollegeAdminKpiCardTone({
  tone,
  index,
  kpiKey,
  label,
}: {
  tone?: CollegeAdminKpiTone;
  index?: number;
  kpiKey?: string;
  label: string;
}): CollegeAdminKpiTone {
  if (tone) return tone;
  if (index !== undefined) return collegeAdminKpiToneForIndex(index);
  return collegeAdminKpiToneForKey(kpiKey ?? label);
}

const KPI_KEY_ICON: Array<{ test: (key: string, label: string) => boolean; icon: ErpIconName }> = [
  { test: (k, l) => k.includes("upload") || l.includes("upload"), icon: "upload" },
  { test: (k, l) => k.includes("import") || l.includes("import"), icon: "download" },
  { test: (k, l) => k.includes("calendar") || l.includes("calendar") || l.includes("semester"), icon: "calendar-days" },
  { test: (k, l) => k.includes("programme") || l.includes("program"), icon: "book-open" },
  { test: (k, l) => k.includes("curriculum") || l.includes("curriculum"), icon: "library-big" },
  { test: (k, l) => k.includes("course") || l.includes("course"), icon: "notebook-text" },
  { test: (k, l) => k === "applications" || (k.includes("application") && !k.includes("admission")), icon: "file-text" },
  { test: (k, l) => k.includes("admission") || l.includes("admission"), icon: "user-plus" },
  { test: (k, l) => k === "under_review" || l.includes("under review"), icon: "clipboard-list" },
  { test: (k, l) => k === "approved" || l === "approved", icon: "circle-check-big" },
  { test: (k, l) => k.includes("rejected") || l.includes("rejected"), icon: "circle-x" },
  { test: (k, l) => k.includes("student") || l.includes("student"), icon: "graduation-cap" },
  { test: (k, l) => k.includes("status_changes") || l.includes("status change"), icon: "refresh-cw" },
  { test: (k, l) => k.includes("faculty") || l.includes("faculty") || l.includes("employee"), icon: "users-round" },
  { test: (k, l) => k.includes("teacher") || l.includes("teacher"), icon: "user-round-cog" },
  { test: (k, l) => k.includes("user") || l.includes("user"), icon: "users" },
  { test: (k, l) => k.includes("role") || l.includes("role"), icon: "shield-check" },
  { test: (k, l) => k.includes("login") || l.includes("login"), icon: "log-in" },
  { test: (k, l) => k.includes("active") || l.includes("active"), icon: "user-check" },
  { test: (k, l) => k.includes("document") || l.includes("document"), icon: "file-check" },
  { test: (k, l) => k.includes("pending") || l.includes("pending") || l.includes("awaiting"), icon: "clock" },
  { test: (k, l) => k.includes("approv"), icon: "square-check" },
  { test: (k, l) => k.includes("alert") || l.includes("warning") || l.includes("attention"), icon: "triangle-alert" },
  { test: (k, l) => k.includes("critical") || l.includes("critical"), icon: "circle-alert" },
  { test: (k, l) => k.includes("finance") || l.includes("fee") || l.includes("revenue") || l.includes("collected"), icon: "wallet" },
  { test: (k, l) => k.includes("attendance") || l.includes("attendance") || l.includes("compliance"), icon: "clipboard-check" },
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
  return <Icon className={className} aria-hidden strokeWidth={1.75} />;
}

function hintToneClass(tone?: string): string | undefined {
  if (tone === "success") return "text-[#047857]";
  if (tone === "warning") return "text-[#c2410c]";
  if (tone === "error" || tone === "danger") return "text-[#dc2626]";
  if (tone === "info") return "text-[#1d4ed8]";
  if (tone === "muted") return undefined;
  return undefined;
}

function valueToneClass(tone?: string): string {
  if (tone === "danger" || tone === "error") return "text-[#dc2626]";
  if (tone === "success") return "text-[#047857]";
  if (tone === "warning") return "text-[#c2410c]";
  return "text-[#0f172a]";
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
  index,
  kpiKey,
  className,
}: CollegeAdminKpiCardProps) {
  const key = kpiKey ?? label;
  const cardTone = resolveCollegeAdminKpiCardTone({ tone, index, kpiKey: key, label });
  const styles = TONE_STYLES[cardTone];
  const slug = iconSlug ?? resolveCollegeAdminKpiIconSlug(key, label);
  const hintClass = hintToneClass(hintTone) ?? styles.hint;
  const resolvedValueTone =
    valueTone ?? (hintTone === "danger" || hintTone === "error" ? hintTone : undefined);

  return (
    <article
      data-college-admin-kpi=""
      className={cn(
        "relative flex min-h-[7.75rem] flex-col justify-between overflow-hidden rounded-[18px] border p-[18px] shadow-[0_2px_8px_rgba(15,23,42,0.04)] transition-[transform,box-shadow] duration-200 hover:-translate-y-0.5 hover:shadow-[0_12px_28px_rgba(15,23,42,0.1)]",
        styles.surface,
        className,
      )}
    >
      <div
        className={cn("pointer-events-none absolute -left-8 -top-8 size-28 rounded-full opacity-25 blur-2xl", styles.glow)}
        aria-hidden
      />

      <div
        className="pointer-events-none absolute -bottom-5 -right-4 opacity-[0.2]"
        aria-hidden
      >
        <ErpKpiIcon slug={slug} className={cn("size-[6.5rem]", styles.watermark)} />
      </div>

      <div className="relative z-[1] flex items-start gap-3.5">
        <div
          className={cn(
            "flex size-11 shrink-0 items-center justify-center rounded-[14px] border border-white/90 bg-white ring-1",
            styles.iconTile,
          )}
        >
          <ErpKpiIcon slug={slug} className={cn("size-5", styles.icon)} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[13px] font-semibold leading-snug text-[#334155]">{label}</p>
          <p
            className={cn(
              "mt-1.5 text-[1.75rem] font-bold leading-none tracking-tight tabular-nums",
              valueToneClass(resolvedValueTone),
            )}
          >
            {value}
          </p>
        </div>
      </div>

      {hint ? (
        <p className={cn("relative z-[1] mt-4 text-[12px] font-medium leading-snug", hintClass)}>{hint}</p>
      ) : (
        <span className="relative z-[1] mt-4 block min-h-[1.125rem]" aria-hidden />
      )}
    </article>
  );
}
CollegeAdminKpiCard.isCollegeAdminKpiCard = true;

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
StatCard.isCollegeAdminKpiCard = true;

function isCollegeAdminKpiGridChild(
  child: ReactNode,
): child is ReactElement<Partial<CollegeAdminKpiCardProps>> {
  if (!isValidElement(child) || typeof child.type !== "function") return false;
  return Boolean(
    (child.type as { isCollegeAdminKpiCard?: boolean }).isCollegeAdminKpiCard,
  );
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
CollegeAdminUserDashboardKpiCard.isCollegeAdminKpiCard = true;

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
CollegeAdminDashboardKpiCard.isCollegeAdminKpiCard = true;

export function CollegeAdminKpiGrid({
  children,
  className,
  columns = 4,
}: {
  children: ReactNode;
  className?: string;
  columns?: 2 | 3 | 4;
}) {
  const colClass =
    columns === 2
      ? "sm:grid-cols-2"
      : columns === 3
        ? "sm:grid-cols-2 lg:grid-cols-3"
        : "sm:grid-cols-2 xl:grid-cols-4";

  const items = Children.toArray(children);

  return (
    <div
      className={cn("grid grid-cols-1 gap-4", colClass, className)}
      data-college-admin-kpi-grid=""
    >
      {items.map((child, position) => {
        if (!isCollegeAdminKpiGridChild(child)) return child;
        const props = child.props;
        if (props.tone !== undefined) return child;
        const nextIndex = props.index ?? position;
        return cloneElement(child, {
          index: nextIndex,
          tone: resolveCollegeAdminKpiCardTone({
            index: nextIndex,
            kpiKey: props.kpiKey,
            label: props.label ?? "",
          }),
        });
      })}
    </div>
  );
}