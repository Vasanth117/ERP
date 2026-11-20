"use client";

import type { ReactNode } from "react";

import { formatDateTime, formatTime } from "@/features/student/components/ui/student-screen-ui";
import type { TimetableSlot } from "@/features/student/types/timetable";

export function TimetableSlotsTable({ slots }: { slots: TimetableSlot[] }) {
  if (slots.length === 0) {
    return <p className="py-8 text-center text-sm text-[#9ca3af]">No timetable slots.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead className="text-xs uppercase text-[#9ca3af]">
          <tr>
            <th className="px-2 py-2">Time</th>
            <th className="px-2 py-2">Course</th>
            <th className="px-2 py-2">Section</th>
            <th className="px-2 py-2">Room</th>
            <th className="px-2 py-2">Type</th>
          </tr>
        </thead>
        <tbody>
          {slots.map((slot) => (
            <tr key={slot.id} className="border-t border-[#f1f5f9]">
              <td className="px-2 py-3 whitespace-nowrap">
                {formatTime(slot.start_time)} – {formatTime(slot.end_time)}
              </td>
              <td className="px-2 py-3">
                <span className="font-medium">{slot.course_code}</span>
                <span className="mt-0.5 block text-xs text-[#6b7280]">{slot.course_name}</span>
              </td>
              <td className="px-2 py-3">{slot.section}</td>
              <td className="px-2 py-3">{slot.room ?? slot.laboratory ?? "—"}</td>
              <td className="px-2 py-3 capitalize">{slot.session_type.replace(/_/g, " ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function EventsList({
  items,
  timeKey = "event_at",
}: {
  items: { id: string; title: string; description?: string | null; [key: string]: unknown }[];
  timeKey?: string;
}) {
  if (items.length === 0) {
    return <p className="py-6 text-center text-sm text-[#9ca3af]">No items.</p>;
  }
  return (
    <ul className="divide-y divide-[#f1f5f9]">
      {items.map((item) => (
        <li key={item.id} className="py-3 text-sm">
          <p className="font-medium text-[#111827]">{item.title}</p>
          {item.description ? (
            <p className="mt-0.5 text-xs text-[#6b7280]">{String(item.description)}</p>
          ) : null}
          {item[timeKey] ? (
            <p className="mt-1 text-xs text-[#9ca3af]">{formatDateTime(String(item[timeKey]))}</p>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

export function DateAnchorField({
  value,
  onChange,
  label = "Anchor date",
}: {
  value: string;
  onChange: (v: string) => void;
  label?: string;
}) {
  return (
    <label className="mb-4 flex max-w-xs flex-col gap-1 text-sm">
      <span className="text-xs font-medium text-[#6b7280]">{label}</span>
      <input
        type="date"
        className="h-10 rounded-lg border border-[#dce3ec] bg-white px-3"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}

export function SimplePanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-[#e8ecf2] bg-white p-4 sm:p-5">
      <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{title}</h3>
      {children}
    </section>
  );
}