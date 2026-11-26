"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { SearchIcon } from "@/components/icons/erp/generated/search";
import { Input } from "@/components/ui/input";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useLibraryBookCataloguePage } from "@/features/college-admin/hooks/use-library-book-catalogue";
import type {
  LibraryBookCataloguePage,
  LibraryBookCataloguePagination,
} from "@/features/college-admin/types/library-book-catalogue";
import { cn } from "@/lib/utils";

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
      className="h-9 min-w-[9rem] rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]"
    >
      {options.map((opt) => (
        <option key={`${opt.value}-${opt.label}`} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

function TablePagination({
  pagination,
  onPage,
}: {
  pagination: LibraryBookCataloguePagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 0) return null;
  return (
    <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Catalogue pagination">
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 text-[12px] disabled:opacity-40"
        disabled={!pagination.has_previous}
        onClick={() => onPage(Math.max(1, pagination.page - 1))}
      >
        ‹
      </button>
      {pagination.page_numbers.map((num, idx) =>
        num === -1 ? (
          <span key={`ellipsis-${idx}`} className="px-1 text-[12px] text-[#9ca3af]">
            …
          </span>
        ) : (
          <button
            key={num}
            type="button"
            onClick={() => onPage(num)}
            className={cn(
              "min-w-[1.75rem] rounded px-1.5 py-0.5 text-[12px] tabular-nums",
              num === pagination.page
                ? "bg-[#245dd8] font-medium text-white"
                : "text-[#6b7280] hover:bg-[#f3f4f6]",
            )}
          >
            {num}
          </button>
        ),
      )}
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 text-[12px] disabled:opacity-40"
        disabled={!pagination.has_next}
        onClick={() => onPage(pagination.page + 1)}
      >
        ›
      </button>
    </nav>
  );
}

const emptyPagination: LibraryBookCataloguePagination = {
  page: 1,
  page_size: 4,
  total: 0,
  total_pages: 0,
  page_numbers: [],
  has_previous: false,
  has_next: false,
};

function mergeView(data: LibraryBookCataloguePage | undefined) {
  return {
    page_title: data?.page_title ?? "",
    page_subtitle: data?.page_subtitle ?? "",
    export_label: data?.export_label ?? "",
    add_title_label: data?.add_title_label ?? "",
    add_title_href: data?.add_title_href ?? "#",
    search_placeholder: data?.search_placeholder ?? "",
    category_filter_label: data?.category_filter_label ?? "Category",
    branch_filter_label: data?.branch_filter_label ?? "Branch",
    category_options: data?.category_options ?? [{ value: "", label: "All categories" }],
    branch_options: data?.branch_options ?? [{ value: "", label: "All branches" }],
    catalogue_section_title: data?.catalogue_section_title ?? "",
    table_headers: data?.table_headers ?? [],
    catalogue_rows: data?.catalogue_rows ?? [],
    empty_table_message: data?.empty_table_message ?? "",
    showing_label: data?.showing_label ?? "",
    pagination: data?.pagination ?? emptyPagination,
  };
}

export function LibraryBookCatalogueDashboard() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [category, setCategory] = useState("");
  const [branchCode, setBranchCode] = useState("");

  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => window.clearTimeout(t);
  }, [search]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, category, branchCode]);

  const queryParams = useMemo(
    () => ({
      page,
      page_size: 4,
      search: debouncedSearch || undefined,
      category: category || undefined,
      branch_code: branchCode || undefined,
    }),
    [page, debouncedSearch, category, branchCode],
  );

  const { data, isLoading, isError, error, refetch, isFetching } = useLibraryBookCataloguePage(queryParams);
  const view = mergeView(data);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `library-catalogue-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <div className="space-y-5" data-figma-frame="160:12220">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {view.page_title || "Book Catalogue"}
          </h2>
          {view.page_subtitle ? (
            <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p>
          ) : null}
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            onClick={handleExport}
            disabled={!data}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
          >
            <CollegeAdminDownload className="size-3.5" />
            {view.export_label || "Export"}
          </button>
          <Link
            href={view.add_title_href}
            className="inline-flex h-9 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <CollegeAdminPlusActionLabel label={view.add_title_label || "Add title"} />
          </Link>
        </div>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:flex-wrap lg:items-center">
        <div className="relative min-w-[14rem] flex-1 lg:max-w-md">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[#9ca3af]" aria-hidden />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={view.search_placeholder}
            className="h-9 border-[#dce3ec] pl-9 text-[13px]"
          />
        </div>
        <FilterSelect
          label={view.category_filter_label}
          value={category}
          onChange={setCategory}
          options={view.category_options}
        />
        <FilterSelect
          label={view.branch_filter_label}
          value={branchCode}
          onChange={setBranchCode}
          options={view.branch_options}
        />
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading catalogue…" : "Updating…"}</p>
      ) : null}

      {isError ? (
        <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
          <></>
        </QueryState>
      ) : !data ? null : (
        <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
          <div className="border-b border-[#f1f5f9] px-5 py-3.5">
            <h3 className="text-[14px] font-semibold text-[#111827]">
              {view.catalogue_section_title || "Book catalogue"}
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[52rem] text-left text-[13px]">
              <thead>
                <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                  {view.table_headers.map((header, index, headers) => (
                    <th
                      key={header}
                      className={cn(
                        "pb-3 pt-4 font-medium",
                        index === 0 ? "pl-5 pr-3" : "pr-3",
                        index === headers.length - 1 ? "pr-5" : "",
                        index >= 4 ? "text-right tabular-nums" : "",
                      )}
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f1f5f9]">
                {view.catalogue_rows.length ? (
                  view.catalogue_rows.map((row) => (
                    <tr key={row.book_id} className="text-[#374151] hover:bg-[#f9fafb]">
                      <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                        <Link href={row.detail_href} className="hover:text-[#245dd8]">
                          {row.title}
                        </Link>
                      </td>
                      <td className="py-3 pr-3 text-[#6b7280] tabular-nums">{row.isbn_label}</td>
                      <td className="py-3 pr-3 text-[#6b7280]">{row.author_label}</td>
                      <td className="py-3 pr-3">{row.category_label}</td>
                      <td className="py-3 pr-3 text-right tabular-nums">{row.copies_label}</td>
                      <td className="py-3 pr-5 text-right tabular-nums">{row.available_label}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td
                      colSpan={Math.max(view.table_headers.length, 1)}
                      className="px-5 py-10 text-center text-sm text-[#9ca3af]"
                    >
                      {view.empty_table_message}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
            <span>{view.showing_label}</span>
            <TablePagination pagination={view.pagination} onPage={setPage} />
          </div>
        </section>
      )}
    </div>
  );
}