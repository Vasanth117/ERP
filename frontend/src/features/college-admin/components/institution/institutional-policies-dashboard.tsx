"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { SearchIcon } from "@/components/icons/erp/generated/search";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useInstitutionPoliciesPage } from "@/features/college-admin/hooks/use-institution";
import type { InstitutionPolicyRow } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    info: "bg-[#3b82f6]",
    muted: "bg-[#9ca3af]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium",
        styles[key],
      )}
    >
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <select
      aria-label={label}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="h-9 min-w-[7.5rem] rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]"
    >
      {options.map((opt) => (
        <option key={`${opt.value}-${opt.label}`} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

function formatSnapshot(iso: string) {
  try {
    return new Intl.DateTimeFormat("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Asia/Kolkata",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function InstitutionalPoliciesDashboard() {
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [category, setCategory] = useState("");
  const [audience, setAudience] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<string | undefined>();

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, category, audience, status]);

  const { data, isLoading, isError, error, refetch } = useInstitutionPoliciesPage({
    search: debouncedSearch || undefined,
    category: category || undefined,
    audience: audience || undefined,
    status: status || undefined,
    page,
    selected_policy_id: selectedId,
  });

  useEffect(() => {
    if (data?.selected_policy && !selectedId) {
      setSelectedId(data.selected_policy.policy_id);
    }
  }, [data?.selected_policy, selectedId]);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `institution-policies-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const pickRow = (row: InstitutionPolicyRow) => {
    setSelectedId(row.policy_id);
  };

  return (
    <div className="space-y-5" data-figma-frame="72:8805">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Institutional Policies"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Policies published to students, faculty and staff"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] text-xs"
            onClick={handleExport}
            disabled={!data}
          >
            <CollegeAdminDownload className="size-3.5" />
            {data?.export_label ?? "Export list"}
          </Button>
          <Link
            href={data?.add_policy_href ?? "#add-policy"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <PlusIcon className="size-3.5" aria-hidden />
            {data?.add_policy_label ?? "Add policy"}
          </Link>
        </div>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative max-w-md flex-1">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[#9ca3af]" />
          <Input
            className="h-9 pl-9"
            placeholder={data?.search_placeholder ?? "Search policies..."}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {data ? (
          <div className="flex flex-wrap gap-2">
            <FilterSelect
              label={data.category_filter_label}
              value={category}
              onChange={setCategory}
              options={data.category_options}
            />
            <FilterSelect
              label={data.audience_filter_label}
              value={audience}
              onChange={setAudience}
              options={data.audience_options}
            />
            <FilterSelect
              label={data.status_filter_label}
              value={status}
              onChange={setStatus}
              options={data.status_options}
            />
          </div>
        ) : null}
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">Policy library</h3>
                </div>
                {data.policies.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[40rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          <th className="px-5 pb-3 font-medium">Policy</th>
                          <th className="pb-3 pr-3 font-medium">Audience</th>
                          <th className="pb-3 pr-3 font-medium">Version</th>
                          <th className="pb-3 pr-3 font-medium">Effective</th>
                          <th className="pb-3 pr-5 font-medium">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.policies.map((row) => (
                          <tr
                            key={row.policy_id}
                            className={cn(
                              "cursor-pointer transition-colors hover:bg-[#f9fafb]",
                              data.selected_policy?.policy_id === row.policy_id && "bg-[#eff6ff]",
                            )}
                            onClick={() => pickRow(row)}
                          >
                            <td className="px-5 py-3 font-medium text-[#111827]">{row.title}</td>
                            <td className="py-3 pr-3 text-[#374151]">{row.audience_label}</td>
                            <td className="py-3 pr-3 tabular-nums">{row.version_label}</td>
                            <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.effective_label}</td>
                            <td className="py-3 pr-5">
                              <StatusPill label={row.status_label} tone={row.status_tone} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-8 text-sm text-[#9ca3af]">No policies match your filters.</p>
                )}
                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  <span>{data.policy_count_label}</span>
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
                      disabled={!data.pagination.has_previous}
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                    >
                      ‹
                    </button>
                    {data.pagination.page_numbers.map((num, index) =>
                      num === -1 ? (
                        <span key={`ellipsis-${index}`} className="px-1">
                          …
                        </span>
                      ) : (
                        <button
                          key={num}
                          type="button"
                          className={cn(
                            "min-w-8 rounded border px-2 py-1 tabular-nums",
                            num === data.pagination.page
                              ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]"
                              : "border-[#dce3ec]",
                          )}
                          onClick={() => setPage(num)}
                        >
                          {num}
                        </button>
                      ),
                    )}
                    <button
                      type="button"
                      className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
                      disabled={!data.pagination.has_next}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      ›
                    </button>
                  </div>
                </div>
              </section>

              <div className="space-y-5">
                {data.selected_policy ? (
                  <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                    <div className="flex items-start justify-between gap-2 border-b border-[#f1f5f9] px-5 py-3.5">
                      <h3 className="text-[14px] font-semibold text-[#111827]">
                        {data.selected_panel_prefix} {data.selected_policy.title}
                      </h3>
                      <Link
                        href={data.selected_policy.open_href}
                        className="shrink-0 text-[12px] font-medium text-[#245dd8] hover:underline"
                      >
                        {data.selected_policy.open_label} →
                      </Link>
                    </div>
                    <dl className="space-y-3 px-5 py-4 text-[13px]">
                      {data.selected_policy.owner_label ? (
                        <div>
                          <dt className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                            Owner
                          </dt>
                          <dd className="mt-1 text-[#111827]">{data.selected_policy.owner_label}</dd>
                        </div>
                      ) : null}
                      {data.selected_policy.approved_by_label ? (
                        <div>
                          <dt className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                            Approved by
                          </dt>
                          <dd className="mt-1 text-[#111827]">{data.selected_policy.approved_by_label}</dd>
                        </div>
                      ) : null}
                      {data.selected_policy.acknowledgement_requirement ? (
                        <div>
                          <dt className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                            Acknowledgement
                          </dt>
                          <dd className="mt-1 text-[#374151]">
                            {data.selected_policy.acknowledgement_requirement}
                          </dd>
                          {data.selected_policy.acknowledgement_progress_label ? (
                            <dd className="mt-1 font-medium tabular-nums text-[#111827]">
                              {data.selected_policy.acknowledgement_progress_label}
                            </dd>
                          ) : null}
                        </div>
                      ) : null}
                    </dl>
                  </section>
                ) : null}

                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">
                      {data.review_schedule_title}
                    </h3>
                  </div>
                  {data.review_schedule.length ? (
                    <ul className="divide-y divide-[#f1f5f9] px-5">
                      {data.review_schedule.map((item) => (
                        <li
                          key={item.review_id}
                          className="flex items-start justify-between gap-2 py-3.5 first:pt-3"
                        >
                          <div>
                            <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
                            <p className="text-[12px] text-[#6b7280]">{item.subtitle}</p>
                          </div>
                          <StatusPill label={item.status_label} tone={item.status_tone} />
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="px-5 py-6 text-sm text-[#9ca3af]">No scheduled reviews.</p>
                  )}
                </section>
              </div>
            </div>

            <footer className="flex flex-col gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
              <p>{data.footer_disclaimer}</p>
              <p className="tabular-nums">
                {data.footer_snapshot_label} · {formatSnapshot(data.generated_at)}
              </p>
            </footer>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}