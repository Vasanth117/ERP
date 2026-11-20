"use client";

import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function SectionPanel({
  title,
  description,
  className,
  children,
  actions,
}: {
  title: string;
  description?: string;
  className?: string;
  children: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <section
      className={`rounded-xl border border-[#dce3ec] bg-white p-5 shadow-[0px_1px_1px_rgba(23,43,69,0.04)] ${className ?? ""}`}
    >
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-sm font-semibold text-[#172b45]">{title}</h2>
          {description ? (
            <p className="mt-1 text-xs text-[#607086]">{description}</p>
          ) : null}
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}

export function ToolbarRow({
  children,
  onRefresh,
}: {
  children?: ReactNode;
  onRefresh?: () => void;
}) {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2">{children}</div>
      {onRefresh ? (
        <Button
          type="button"
          variant="outline"
          className="h-9 border-[#dce3ec] text-xs"
          onClick={onRefresh}
        >
          Refresh
        </Button>
      ) : null}
    </div>
  );
}

export function SearchField({
  value,
  onChange,
  placeholder = "Search…",
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <Input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="h-9 max-w-xs border-[#dce3ec] bg-white text-sm"
    />
  );
}

export function DataTable({
  columns,
  rows,
  emptyMessage = "No records found.",
}: {
  columns: string[];
  rows: Record<string, unknown>[];
  emptyMessage?: string;
}) {
  if (rows.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-[#dce3ec] px-4 py-8 text-center text-sm text-[#607086]">
        {emptyMessage}
      </p>
    );
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead className="border-b border-[#eceff4] bg-[#f8fafc] text-[11px] uppercase tracking-wide text-[#8a98aa]">
          <tr>
            {columns.map((c) => (
              <th key={c} className="px-4 py-3 font-semibold">
                {c.replace(/_/g, " ")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-[#eceff4] last:border-0">
              {columns.map((c) => (
                <td key={c} className="px-4 py-3 text-[#172b45]">
                  {formatCell(row[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatCell(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value).slice(0, 80);
  return String(value);
}

export function FormPlaceholder({
  title,
  description,
  submitLabel = "Save changes",
}: {
  title: string;
  description: string;
  submitLabel?: string;
}) {
  return (
    <SectionPanel title={title} description={description}>
      <div className="grid max-w-xl gap-4">
        <label className="grid gap-1 text-xs text-[#607086]">
          Field placeholder
          <Input disabled className="border-[#dce3ec]" placeholder="Enter value" />
        </label>
        <label className="grid gap-1 text-xs text-[#607086]">
          Notes
          <Input disabled className="border-[#dce3ec]" placeholder="Optional" />
        </label>
        <Button
          type="button"
          disabled
          className="h-9 w-fit bg-[#245dd8] text-xs hover:bg-[#1f4fb8]"
        >
          {submitLabel}
        </Button>
        <p className="text-xs text-[#8a98aa]">
          Form fields will mirror the Figma screen layout when design context is synced for this
          frame.
        </p>
      </div>
    </SectionPanel>
  );
}

export function DetailGrid({ record }: { record: Record<string, unknown> }) {
  const entries = Object.entries(record).slice(0, 24);
  return (
    <dl className="grid gap-3 sm:grid-cols-2">
      {entries.map(([key, value]) => (
        <div
          key={key}
          className="rounded-lg border border-[#eceff4] bg-[#f8fafc] px-3 py-2"
        >
          <dt className="text-[10px] font-semibold uppercase tracking-wide text-[#8a98aa]">
            {key.replace(/_/g, " ")}
          </dt>
          <dd className="mt-1 text-sm text-[#172b45]">{formatCell(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

export function rowsFromApi(data: unknown): Record<string, unknown>[] {
  if (Array.isArray(data)) {
    return data.filter((x) => x && typeof x === "object") as Record<string, unknown>[];
  }
  if (data && typeof data === "object") {
    const obj = data as Record<string, unknown>;
    if (Array.isArray(obj.items)) {
      return obj.items.filter((x) => x && typeof x === "object") as Record<
        string,
        unknown
      >[];
    }
    if (Array.isArray(obj.data)) {
      return obj.data.filter((x) => x && typeof x === "object") as Record<
        string,
        unknown
      >[];
    }
    if (Array.isArray(obj.records)) {
      return obj.records.filter((x) => x && typeof x === "object") as Record<
        string,
        unknown
      >[];
    }
    const scalarKeys = ["total", "limit", "offset", "count"];
    const rowKeys = Object.keys(obj).filter((k) => !scalarKeys.includes(k));
    if (rowKeys.length > 0 && rowKeys.every((k) => typeof obj[k] !== "object")) {
      return [obj];
    }
    return [obj];
  }
  return [];
}

export function columnsFromRows(rows: Record<string, unknown>[]): string[] {
  if (!rows.length) return [];
  return Object.keys(rows[0]).slice(0, 8);
}