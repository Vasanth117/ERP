"use client";

import Link from "next/link";

import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import {
  StAcademicsDetailField,
  StAcademicsOutcomeBadge,
  StAcademicsSectionCard,
} from "@/features/student/components/ui/student-academics-figma-ui";
import { formatTime } from "@/features/student/components/ui/student-screen-ui";
import type {
  TimetableCourseFilterOption,
  TimetableDailySessionRow,
  TimetableSessionDetail,
} from "@/features/student/types/timetable";
import { cn } from "@/lib/utils";

export function TimetableCourseFilter({
  options,
  value,
  onChange,
}: {
  options: TimetableCourseFilterOption[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="flex min-w-0 flex-col gap-1 text-[12px] text-[#6b7280]">
      <span className="font-medium">Course</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-8 max-w-[200px] rounded border border-[#e8ecf2] bg-white px-2 text-[13px] text-[#172b45]"
      >
        {options.map((o) => (
          <option key={o.value || "all"} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function TimetableDateNav({
  subtitle,
  prevHref,
  nextHref,
}: {
  subtitle: string;
  prevHref: string;
  nextHref: string;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <p className="text-[13px] text-[#6b7280]">{subtitle}</p>
      <div className="flex items-center gap-1">
        <Link
          href={prevHref}
          className="inline-flex size-8 items-center justify-center rounded-md border border-[#e8ecf2] bg-white text-[#172b45] hover:bg-[#f8fafc]"
          aria-label="Previous day"
        >
          <ChevronLeftIcon className="size-4 stroke-[2]" />
        </Link>
        <Link
          href={nextHref}
          className="inline-flex size-8 items-center justify-center rounded-md border border-[#e8ecf2] bg-white text-[#172b45] hover:bg-[#f8fafc]"
          aria-label="Next day"
        >
          <ChevronRightIcon className="size-4 stroke-[2]" />
        </Link>
      </div>
    </div>
  );
}

export function TimetableSessionTimeline({
  rows,
  selectedSlotId,
  onSelect,
  footer,
}: {
  rows: TimetableDailySessionRow[];
  selectedSlotId: string | null;
  onSelect: (slotId: string) => void;
  footer?: string;
}) {
  return (
    <StAcademicsSectionCard title="Sessions" footer={footer ? <span>{footer}</span> : undefined}>
      {rows.length === 0 ? (
        <p className="px-4 py-8 text-center text-[13px] text-[#9ca3af]">No sessions scheduled.</p>
      ) : (
        <ul className="grid gap-1.5 px-3 py-2">
          {rows.map((row) => {
            const selected = selectedSlotId === row.slot_id;
            return (
              <li key={row.slot_id}>
                <button
                  type="button"
                  onClick={() => onSelect(row.slot_id)}
                  className={cn(
                    "flex w-full gap-3 rounded-md border px-2.5 py-2 text-left text-[13px] transition-colors",
                    selected
                      ? "border-[#245dd8] bg-[#eff6ff]"
                      : "border-[#e8ecf2] hover:border-[#c5d4f0] hover:bg-[#f8fafc]",
                  )}
                >
                  <span className="w-[4.5rem] shrink-0 tabular-nums text-[#6b7280]">
                    {formatTime(row.start_time)}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block font-medium text-[#172b45]">{row.subject_label}</span>
                    <span className="mt-0.5 block text-[12px] text-[#6b7280]">
                      {row.course_code} · {row.session_type_label} · {row.room_label}
                    </span>
                  </span>
                  <StAcademicsOutcomeBadge label={row.status_label} tone={row.status_tone} />
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </StAcademicsSectionCard>
  );
}

export function TimetableSessionDetailPanel({
  detail,
  figmaNode = "164:15581",
}: {
  detail: TimetableSessionDetail | null;
  figmaNode?: string;
}) {
  return (
    <StAcademicsSectionCard title={detail?.panel_title ?? "Class session details"}>
      <div data-figma-frame={figmaNode}>
        {!detail ? (
          <p className="px-4 py-6 text-center text-[13px] text-[#9ca3af]">
            Select a session to view details.
          </p>
        ) : (
          <div className="px-4 py-3">
            <p className="text-[14px] font-semibold text-[#172b45]">{detail.headline}</p>
            {detail.subheadline ? (
              <p className="mt-0.5 text-[12px] text-[#6b7280]">{detail.subheadline}</p>
            ) : null}
            <dl className="mt-3 grid gap-2 sm:grid-cols-2">
              {detail.fields.map((field) => (
                <StAcademicsDetailField key={field.label} label={field.label} value={field.value} />
              ))}
            </dl>
          </div>
        )}
      </div>
    </StAcademicsSectionCard>
  );
}

export function buildTimetableQueryPath(
  base: string,
  params: { view?: string; date?: string; course?: string; slot?: string },
) {
  const qs = new URLSearchParams();
  if (params.view) qs.set("view", params.view);
  if (params.date) qs.set("date", params.date);
  if (params.course) qs.set("course", params.course);
  if (params.slot) qs.set("slot", params.slot);
  const q = qs.toString();
  return q ? `${base}?${q}` : base;
}

/** ST 05.02 — daily table (164:14917). */
export function TimetableDaySessionsTable({
  title = "Today",
  rows,
  selectedSlotId,
  onSelect,
  footer,
}: {
  title?: string;
  rows: TimetableDailySessionRow[];
  selectedSlotId: string | null;
  onSelect: (slotId: string) => void;
  footer?: string;
}) {
  return (
    <StAcademicsSectionCard title={title} footer={footer ? <span>{footer}</span> : undefined}>
      {rows.length === 0 ? (
        <p className="px-4 py-8 text-center text-[13px] text-[#9ca3af]">No sessions scheduled.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-[13px]">
            <thead>
              <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
                <th className="px-4 py-2.5">Time</th>
                <th className="px-4 py-2.5">Subject</th>
                <th className="px-4 py-2.5">Type</th>
                <th className="px-4 py-2.5">Room</th>
                <th className="px-4 py-2.5">Faculty</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e8ecf2]">
              {rows.map((row) => {
                const selected = selectedSlotId === row.slot_id;
                return (
                  <tr
                    key={row.slot_id}
                    className={cn(
                      "cursor-pointer text-[#172b45] transition-colors",
                      selected ? "bg-[#eff6ff]" : "hover:bg-[#f8fafc]",
                    )}
                    onClick={() => onSelect(row.slot_id)}
                  >
                    <td className="whitespace-nowrap px-4 py-2.5 tabular-nums text-[#6b7280]">
                      {formatTime(row.start_time)} – {formatTime(row.end_time)}
                    </td>
                    <td className="px-4 py-2.5 font-medium">{row.subject_label}</td>
                    <td className="px-4 py-2.5">{row.session_type_label}</td>
                    <td className="px-4 py-2.5">{row.room_label}</td>
                    <td className="px-4 py-2.5">{row.faculty_label}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </StAcademicsSectionCard>
  );
}

/** ST 05.03 — weekly grid (164:15251). */
export function TimetableWeeklyGrid({
  days,
  selectedSlotId,
  onSelect,
  footer,
}: {
  days: {
    anchor_date: string;
    day_label: string;
    short_label: string;
    slots: TimetableDailySessionRow[];
  }[];
  selectedSlotId: string | null;
  onSelect: (slotId: string, dayDate: string) => void;
  footer?: string;
}) {
  const weekdays = days.slice(0, 5);
  const timeKeys = Array.from(
    new Set(weekdays.flatMap((d) => d.slots.map((s) => s.start_time))),
  ).sort();

  return (
    <StAcademicsSectionCard
      title={days[0] ? `Week of ${weekdays[0]?.short_label}` : "Week"}
      footer={footer ? <span>{footer}</span> : undefined}
    >
      {timeKeys.length === 0 ? (
        <p className="px-4 py-8 text-center text-[13px] text-[#9ca3af]">No sessions this week.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] border-collapse text-[13px]">
            <thead>
              <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase text-[#6b7280]">
                <th className="px-3 py-2 text-left">Time</th>
                {weekdays.map((d) => (
                  <th key={d.anchor_date} className="px-3 py-2 text-left">
                    {d.day_label.slice(0, 3)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {timeKeys.map((timeKey) => (
                <tr key={timeKey} className="border-b border-[#f1f5f9]">
                  <td className="whitespace-nowrap px-3 py-2 tabular-nums text-[#6b7280]">
                    {formatTime(timeKey)}
                  </td>
                  {weekdays.map((day) => {
                    const slot = day.slots.find((s) => s.start_time === timeKey);
                    if (!slot) {
                      return (
                        <td key={day.anchor_date} className="px-3 py-2 text-[12px] text-[#9ca3af]">
                          Free
                        </td>
                      );
                    }
                    const selected = selectedSlotId === slot.slot_id;
                    return (
                      <td key={day.anchor_date} className="px-3 py-2">
                        <button
                          type="button"
                          onClick={() => onSelect(slot.slot_id, day.anchor_date)}
                          className={cn(
                            "max-w-full truncate text-left text-[12px] font-medium",
                            selected ? "text-[#245dd8]" : "text-[#172b45] hover:text-[#245dd8]",
                          )}
                          title={slot.subject_label}
                        >
                          {slot.subject_label.split(" ")[0] ?? slot.course_code}
                        </button>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </StAcademicsSectionCard>
  );
}

/** ST 05.05 — fixed footer session details (164:15581). */
export function TimetableClassSessionDetailsSection({
  detail,
  isLoading,
  isError,
  onClearSelection,
}: {
  detail: TimetableSessionDetail | null;
  isLoading?: boolean;
  isError?: boolean;
  onClearSelection?: () => void;
}) {
  return (
    <section className="mt-4 border-t border-[#e8ecf2] pt-4" data-figma-frame="164:15581">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {onClearSelection ? (
            <button
              type="button"
              onClick={onClearSelection}
              className="inline-flex size-8 items-center justify-center rounded-md border border-[#e8ecf2] bg-white text-[#172b45] hover:bg-[#f8fafc]"
              aria-label="Clear session selection"
            >
              <ChevronLeftIcon className="size-4 stroke-[2]" />
            </button>
          ) : null}
          <div>
            <h3 className="text-[15px] font-semibold text-[#172b45]">
              {detail?.panel_title ?? "Class session details"}
            </h3>
            {detail?.subheadline ? (
              <p className="text-[12px] text-[#6b7280]">{detail.subheadline}</p>
            ) : (
              <p className="text-[12px] text-[#9ca3af]">Select a session above to view details</p>
            )}
          </div>
        </div>
      </div>

      {isLoading ? (
        <StAcademicsSectionCard title="Session">
          <p className="px-4 py-8 text-center text-[13px] text-[#6b7280]">Loading session details…</p>
        </StAcademicsSectionCard>
      ) : isError ? (
        <StAcademicsSectionCard title="Session">
          <p className="px-4 py-8 text-center text-[13px] text-[#b45309]">
            Could not load session details. Try selecting the session again.
          </p>
        </StAcademicsSectionCard>
      ) : detail ? (
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1.4fr)_minmax(220px,1fr)]">
          <StAcademicsSectionCard title="Session">
            <p className="px-4 pt-3 text-[14px] font-semibold text-[#172b45]">{detail.headline}</p>
            <dl className="grid gap-2 px-4 py-3 sm:grid-cols-2 lg:grid-cols-3">
              {detail.fields.map((field) => (
                <StAcademicsDetailField key={field.label} label={field.label} value={field.value} />
              ))}
            </dl>
          </StAcademicsSectionCard>
          <StAcademicsSectionCard title="Related">
            <p className="px-4 py-6 text-center text-[12px] text-[#9ca3af]">
              Linked materials appear when configured for this course.
            </p>
          </StAcademicsSectionCard>
        </div>
      ) : (
        <StAcademicsSectionCard title="Session">
          <p className="px-4 py-8 text-center text-[13px] text-[#9ca3af]">
            Choose a class from the timetable to see session information here.
          </p>
        </StAcademicsSectionCard>
      )}
    </section>
  );
}