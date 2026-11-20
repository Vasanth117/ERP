"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { UploadIcon } from "@/components/icons/erp/generated/upload";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useImportInstitutionCalendarHolidays,
  useInstitutionCalendarSettingsPage,
  useSaveInstitutionCalendarSettingsPage,
} from "@/features/college-admin/hooks/use-institution";
import type {
  InstitutionCalendarFormValues,
  InstitutionCalendarToggleRule,
  InstitutionFieldMeta,
  InstitutionFieldOption,
} from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

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

function SelectField({
  meta,
  options,
  value,
  onChange,
}: {
  meta: InstitutionFieldMeta;
  options: InstitutionFieldOption[];
  value: string;
  onChange: (next: string) => void;
}) {
  return (
    <div>
      <Label className="text-[13px] text-[#374151]">
        {meta.label}
        {meta.required ? <span className="text-[#dc2626]"> *</span> : null}
      </Label>
      <select
        className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((opt) => (
          <option key={opt.value || opt.label} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function ToggleRow({
  rule,
  checked,
  onChange,
}: {
  rule: InstitutionCalendarToggleRule;
  checked: boolean;
  onChange: (next: boolean) => void;
}) {
  return (
    <div className="flex items-start justify-between gap-3 py-3.5 first:pt-1">
      <div>
        <p className="text-[13px] font-medium text-[#111827]">{rule.label}</p>
        {rule.description ? (
          <p className="text-[12px] text-[#6b7280]">{rule.description}</p>
        ) : null}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={cn(
          "relative h-6 w-11 shrink-0 rounded-full transition-colors",
          checked ? "bg-[#245dd8]" : "bg-[#d1d5db]",
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 size-5 rounded-full bg-white shadow transition-transform",
            checked ? "left-[22px]" : "left-0.5",
          )}
        />
      </button>
    </div>
  );
}

export function InstitutionalCalendarSettingsDashboard() {
  const [page, setPage] = useState(1);
  const [academicYearId, setAcademicYearId] = useState<string | undefined>();
  const { data, isLoading, isError, error, refetch } = useInstitutionCalendarSettingsPage({
    page,
    academic_year_id: academicYearId,
  });

  useEffect(() => {
    if (data?.selected_academic_year_id) {
      setAcademicYearId(data.selected_academic_year_id);
    }
  }, [data?.selected_academic_year_id]);

  const saveContext = useMemo(
    () => ({
      page,
      academic_year_id: data?.selected_academic_year_id,
    }),
    [page, data?.selected_academic_year_id],
  );

  const save = useSaveInstitutionCalendarSettingsPage(saveContext);
  const importHolidays = useImportInstitutionCalendarHolidays();

  const form = useForm<InstitutionCalendarFormValues>({
    defaultValues: data?.form,
  });

  useEffect(() => {
    if (data?.form) {
      form.reset(data.form);
    }
  }, [data?.form, form]);

  const submit = form.handleSubmit((values) => save.mutate(values));

  const headers = data?.holiday_table_headers ?? [];
  const [h0, h1, h2, h3] = headers;

  return (
    <div className="space-y-5" data-figma-frame="72:9653">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Institutional Calendar Settings"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] text-xs"
            disabled={importHolidays.isPending}
            onClick={() => importHolidays.mutate()}
          >
            <UploadIcon className="size-3.5" aria-hidden />
            {data?.import_holidays_label ?? "Import holidays"}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs hover:bg-[#1f4fb8]"
            disabled={!data || save.isPending}
            onClick={() => void submit()}
          >
            <CheckIcon className="size-3.5" aria-hidden />
            {data?.save_label ?? "Save settings"}
          </Button>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <form onSubmit={submit} className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.holidays_section_title}</h3>
                <Link
                  href={data.add_holiday_href}
                  className="text-[12px] font-medium text-[#245dd8] hover:underline"
                >
                  {data.add_holiday_label} →
                </Link>
              </div>
              {data.holidays.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[36rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        <th className="px-5 pb-3 font-medium">{h0 ?? "Holiday"}</th>
                        <th className="pb-3 pr-3 font-medium">{h1 ?? "Date"}</th>
                        <th className="pb-3 pr-3 font-medium">{h2 ?? "Type"}</th>
                        <th className="pb-3 pr-5 font-medium">{h3 ?? "Applies to"}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.holidays.map((row) => (
                        <tr key={row.holiday_id} className="hover:bg-[#f9fafb]">
                          <td className="px-5 py-3 font-medium text-[#111827]">{row.title}</td>
                          <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.date_label}</td>
                          <td className="py-3 pr-3 text-[#374151]">{row.type_label}</td>
                          <td className="py-3 pr-5 text-[#374151]">{row.applies_to_label}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-8 text-sm text-[#9ca3af]">No holidays for this academic year yet.</p>
              )}
              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                <span>{data.holiday_count_label}</span>
                {data.pagination.total_pages > 0 ? (
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
                ) : null}
              </div>
            </section>

            <div className="space-y-5">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.working_week_title}</h3>
                </div>
                <div className="grid gap-4 px-5 py-4">
                  <SelectField
                    meta={data.working_days_meta}
                    options={data.working_days_options}
                    value={form.watch("working_days")}
                    onChange={(v) => form.setValue("working_days", v, { shouldDirty: true })}
                  />
                  <SelectField
                    meta={data.saturday_pattern_meta}
                    options={data.saturday_pattern_options}
                    value={form.watch("saturday_pattern")}
                    onChange={(v) => form.setValue("saturday_pattern", v, { shouldDirty: true })}
                  />
                  <SelectField
                    meta={data.day_start_meta}
                    options={data.time_options}
                    value={form.watch("day_start")}
                    onChange={(v) => form.setValue("day_start", v, { shouldDirty: true })}
                  />
                  <SelectField
                    meta={data.day_end_meta}
                    options={data.time_options}
                    value={form.watch("day_end")}
                    onChange={(v) => form.setValue("day_end", v, { shouldDirty: true })}
                  />
                </div>
              </section>

              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.publishing_title}</h3>
                </div>
                <div className="divide-y divide-[#f1f5f9] px-5">
                  {data.publishing_toggles.map((rule) => (
                    <ToggleRow
                      key={rule.key}
                      rule={rule}
                      checked={Boolean(
                        form.watch(rule.key as keyof InstitutionCalendarFormValues),
                      )}
                      onChange={(next) =>
                        form.setValue(rule.key as keyof InstitutionCalendarFormValues, next as never, {
                          shouldDirty: true,
                        })
                      }
                    />
                  ))}
                </div>
              </section>
            </div>

            <div className="col-span-full flex flex-col gap-3 border-t border-[#e8ecf2] pt-4 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-[12px] text-[#6b7280]">{data.footer_note}</p>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    if (data.form) form.reset(data.form);
                  }}
                >
                  {data.cancel_label}
                </Button>
                <Button
                  type="submit"
                  className="bg-[#245dd8] hover:bg-[#1f4fb8]"
                  disabled={save.isPending}
                >
                  {data.save_label}
                </Button>
              </div>
            </div>

            <footer className="col-span-full flex flex-col gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
              <p>{data.footer_disclaimer}</p>
              <p className="tabular-nums">
                {data.footer_snapshot_label} · {formatSnapshot(data.generated_at)}
              </p>
            </footer>
          </form>
        ) : null}
      </QueryState>
    </div>
  );
}