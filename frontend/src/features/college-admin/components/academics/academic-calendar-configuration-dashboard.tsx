"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { SendIcon } from "@/components/icons/erp/generated/send";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { YearsSemestersSubNav } from "@/features/college-admin/components/academics/years-semesters-sub-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAcademicCalendarConfigurationPage,
  useAddAcademicCalendarEvent,
  usePublishAcademicCalendarConfiguration,
} from "@/features/college-admin/hooks/use-academic-calendar-configuration";
import type { AcademicCalendarConfigurationPage } from "@/features/college-admin/types/academic-calendar-configuration";
import type { InstitutionFieldMeta, InstitutionFieldOption } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      {label}
    </span>
  );
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
      <Label className="text-[12px] text-[#374151]">
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

export function AcademicCalendarConfigurationDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const initialView = searchParams.get("view") ?? "list";
  const initialPage = Number(searchParams.get("page") ?? "1");

  const [view, setView] = useState(initialView);
  const [page, setPage] = useState(Number.isFinite(initialPage) && initialPage > 0 ? initialPage : 1);
  const [yearId, setYearId] = useState<string | undefined>();
  const [termId, setTermId] = useState<string | undefined>();

  const queryParams = useMemo(
    () => ({
      view,
      page,
      academic_year_id: yearId,
      term_id: termId,
    }),
    [view, page, yearId, termId],
  );

  const { data, isLoading, isError, error, refetch } = useAcademicCalendarConfigurationPage(queryParams);
  const addEvent = useAddAcademicCalendarEvent();
  const publishCal = usePublishAcademicCalendarConfiguration();

  const formMeta = data?.add_event_form;

  const [title, setTitle] = useState("");
  const [eventType, setEventType] = useState("academic");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [audience, setAudience] = useState("all");

  useEffect(() => {
    if (data?.selected_academic_year_id) setYearId(data.selected_academic_year_id);
    if (data?.selected_term_id) setTermId(data.selected_term_id ?? undefined);
    if (data?.active_view) setView(data.active_view);
  }, [data?.selected_academic_year_id, data?.selected_term_id, data?.active_view]);

  useEffect(() => {
    if (!formMeta) return;
    setEventType(formMeta.type_default_value);
    setAudience(formMeta.audience_default_value);
  }, [formMeta]);

  const syncUrl = (nextView: string, nextPage: number) => {
    const params = new URLSearchParams();
    if (nextView !== "list") params.set("view", nextView);
    if (nextPage > 1) params.set("page", String(nextPage));
    const q = params.toString();
    router.replace(q ? `?${q}` : "?", { scroll: false });
  };

  const pickView = (key: string) => {
    setView(key);
    setPage(1);
    syncUrl(key, 1);
  };

  const handlePublish = () => {
    if (!data?.selected_academic_year_id) return;
    publishCal.mutate({
      academic_year_id: data.selected_academic_year_id,
      calendar_id: data.primary_calendar_id,
    });
  };

  const handleAddEvent = () => {
    if (!data?.selected_academic_year_id || !title.trim() || !fromDate) return;
    addEvent.mutate(
      {
        academic_year_id: data.selected_academic_year_id,
        title: title.trim(),
        event_type: eventType,
        from_date: fromDate,
        to_date: toDate.trim() || null,
        audience,
      },
      {
        onSuccess: () => {
          setTitle("");
          setFromDate("");
          setToDate("");
        },
      },
    );
  };

  return (
    <div className="space-y-5" data-figma-frame="69:142093">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Academic Calendar Configuration"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            disabled={!data?.can_publish || publishCal.isPending}
            onClick={handlePublish}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
          >
            <SendIcon className="size-3.5" aria-hidden />
            {data?.publish_button_label ?? "Publish calendar"}
          </button>
          <a
            href="#add-event-form"
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <PlusIcon className="size-3.5" aria-hidden />
            {data?.add_event_button_label ?? "Add event"}
          </a>
        </div>
      </div>

      {data?.sub_nav?.length ? <YearsSemestersSubNav items={data.sub_nav} /> : null}

      {data?.view_tabs?.length ? (
        <div className="inline-flex rounded-full border border-[#e8ecf2] bg-[#f3f4f6] p-1">
          {data.view_tabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => pickView(tab.key)}
              className={cn(
                "rounded-full px-4 py-1.5 text-[13px] font-medium transition-colors",
                tab.active || view === tab.key ? "bg-white text-[#245dd8] shadow-sm" : "text-[#6b7280] hover:text-[#374151]",
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
      ) : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <div className="grid gap-5 lg:grid-cols-3">
            <section className="lg:col-span-2 overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.list_panel_title}</h3>
              </div>
              {data.event_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[40rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.table_headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn("pb-3 pt-4 font-medium", index === 0 ? "px-5" : "pr-3", index === data.table_headers.length - 1 ? "pr-5" : "")}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.event_rows.map((row) => (
                        <tr key={row.event_id} className="hover:bg-[#f9fafb]">
                          <td className="px-5 py-3 font-medium text-[#111827]">{row.title}</td>
                          <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.date_label}</td>
                          <td className="py-3 pr-3">{row.type_label}</td>
                          <td className="py-3 pr-3">{row.audience_label}</td>
                          <td className="py-3 pr-5">
                            <StatusPill label={row.status_label} tone={row.status_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-10 text-sm text-[#9ca3af]">No calendar events in this view yet. Add an event or configure semester milestones.</p>
              )}
              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                <span>{data.year_event_count_label}</span>
                {data.pagination.total_pages > 0 ? (
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
                      disabled={!data.pagination.has_previous}
                      onClick={() => {
                        const next = Math.max(1, page - 1);
                        setPage(next);
                        syncUrl(view, next);
                      }}
                    >
                      ‹
                    </button>
                    {data.pagination.page_numbers.map((num, index) =>
                      num === -1 ? (
                        <span key={`e-${index}`} className="px-1">
                          …
                        </span>
                      ) : (
                        <button
                          key={num}
                          type="button"
                          className={cn(
                            "min-w-8 rounded border px-2 py-1 tabular-nums",
                            num === data.pagination.page ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]" : "border-[#dce3ec]",
                          )}
                          onClick={() => {
                            setPage(num);
                            syncUrl(view, num);
                          }}
                        >
                          {num}
                        </button>
                      ),
                    )}
                    <button
                      type="button"
                      className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
                      disabled={!data.pagination.has_next}
                      onClick={() => {
                        const next = page + 1;
                        setPage(next);
                        syncUrl(view, next);
                      }}
                    >
                      ›
                    </button>
                  </div>
                ) : null}
              </div>
            </section>

            <CalendarSidebar
              data={data}
              formMeta={formMeta}
              title={title}
              setTitle={setTitle}
              eventType={eventType}
              setEventType={setEventType}
              fromDate={fromDate}
              setFromDate={setFromDate}
              toDate={toDate}
              setToDate={setToDate}
              audience={audience}
              setAudience={setAudience}
              onSubmit={handleAddEvent}
              pending={addEvent.isPending}
            />
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}

function CalendarSidebar({
  data,
  formMeta,
  title,
  setTitle,
  eventType,
  setEventType,
  fromDate,
  setFromDate,
  toDate,
  setToDate,
  audience,
  setAudience,
  onSubmit,
  pending,
}: {
  data: AcademicCalendarConfigurationPage;
  formMeta: AcademicCalendarConfigurationPage["add_event_form"] | undefined;
  title: string;
  setTitle: (v: string) => void;
  eventType: string;
  setEventType: (v: string) => void;
  fromDate: string;
  setFromDate: (v: string) => void;
  toDate: string;
  setToDate: (v: string) => void;
  audience: string;
  setAudience: (v: string) => void;
  onSubmit: () => void;
  pending: boolean;
}) {
  return (
    <div className="flex flex-col gap-5 max-lg:contents lg:col-span-1">
      <section
        id="add-event-form"
        className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]"
      >
        <h3 className="text-[14px] font-semibold text-[#111827]">Add event</h3>
        {formMeta ? (
          <form
            className="mt-4 space-y-3"
            onSubmit={(e) => {
              e.preventDefault();
              onSubmit();
            }}
          >
            <div>
              <Label className="text-[12px] text-[#374151]">
                {formMeta.title_meta.label}
                {formMeta.title_meta.required ? <span className="text-[#dc2626]"> *</span> : null}
              </Label>
              <Input
                className="mt-1.5 h-9"
                placeholder={formMeta.title_placeholder}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>
            <SelectField meta={formMeta.type_meta} options={formMeta.type_options} value={eventType} onChange={setEventType} />
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-[12px] text-[#374151]">
                  {formMeta.from_meta.label}
                  {formMeta.from_meta.required ? <span className="text-[#dc2626]"> *</span> : null}
                </Label>
                <Input className="mt-1.5 h-9" type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
              </div>
              <div>
                <Label className="text-[12px] text-[#374151]">{formMeta.to_meta.label}</Label>
                <Input className="mt-1.5 h-9" type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
              </div>
            </div>
            <SelectField meta={formMeta.audience_meta} options={formMeta.audience_options} value={audience} onChange={setAudience} />
            <button
              type="submit"
              disabled={pending || !title.trim() || !fromDate}
              className="mt-2 h-9 w-full rounded-md bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
            >
              {formMeta.submit_label}
            </button>
          </form>
        ) : null}
      </section>

      <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
        <h3 className="text-[14px] font-semibold text-[#111827]">{data.type_stats_title}</h3>
        <div className="mt-4 space-y-4">
          {data.type_stats.map((row) => (
            <div key={row.type_label}>
              <div className="mb-1.5 flex items-center justify-between text-[12px]">
                <span className="text-[#374151]">{row.type_label}</span>
                <span className="tabular-nums text-[#6b7280]">{row.count}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-[#e8ecf2]">
                <div className="h-full rounded-full bg-[#245dd8]" style={{ width: `${row.bar_percent}%` }} />
              </div>
            </div>
          ))}
          {!data.type_stats.length ? <p className="text-[12px] text-[#9ca3af]">No events recorded for this academic year yet.</p> : null}
        </div>
      </section>
    </div>
  );
}