"use client";

import { useRouter, useSearchParams } from "next/navigation";

import {
  TIMETABLE_SCHEDULE_PATH,
  TIMETABLE_VIEW_OPTIONS,
  parseTimetableView,
} from "@/features/student/config/timetable-schedule";
import { buildTimetableQueryPath } from "@/features/student/components/timetable/timetable-view-ui";
import { cn } from "@/lib/utils";

/** ST 05 — Day | Week | Month | Laboratory on one timetable page (in-page, not module tabs). */
export function TimetableViewSegment({ className }: { className?: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeView = parseTimetableView(searchParams.get("view"));

  const switchView = (view: typeof TIMETABLE_VIEW_OPTIONS[number]["key"]) => {
    const date = searchParams.get("date")?.trim() || undefined;
    const course = searchParams.get("course")?.trim() || undefined;
    const slot = searchParams.get("slot")?.trim() || undefined;
    router.push(
      buildTimetableQueryPath(TIMETABLE_SCHEDULE_PATH, { view, date, course }),
    );
  };

  return (
    <div
      className={cn("inline-flex rounded-lg bg-[#eceff4] p-0.5", className)}
      role="tablist"
      aria-label="Timetable view"
    >
      {TIMETABLE_VIEW_OPTIONS.map((view) => {
        const selected = activeView === view.key;
        return (
          <button
            key={view.key}
            type="button"
            role="tab"
            aria-selected={selected}
            onClick={() => switchView(view.key)}
            className={cn(
              "rounded-md px-3.5 py-1.5 text-[13px] font-medium transition-colors",
              selected
                ? "bg-white text-[#172b45] shadow-[0_1px_2px_rgba(23,43,69,0.08)]"
                : "text-[#6b7280] hover:text-[#172b45]",
            )}
          >
            {view.label}
          </button>
        );
      })}
    </div>
  );
}