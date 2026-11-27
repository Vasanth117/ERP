"use client";

import { useCallback, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import {
  TimetableClassSessionDetailsSection,
  TimetableCourseFilter,
  TimetableDateNav,
  TimetableDaySessionsTable,
  TimetableWeeklyGrid,
  buildTimetableQueryPath,
} from "@/features/student/components/timetable/timetable-view-ui";
import { TimetableViewSegment } from "@/features/student/components/ui/timetable-view-segment";
import { StAcademicsPageBlock, StAcademicsSectionCard } from "@/features/student/components/ui/student-academics-figma-ui";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import {
  TIMETABLE_SCHEDULE_PATH,
  parseTimetableView,
  type TimetableViewKey,
} from "@/features/student/config/timetable-schedule";
import {
  useTimetableDailyPage,
  useTimetableLaboratoryPage,
  useTimetableMonthlyPage,
  useTimetableSessionDetail,
  useTimetableWeeklyPage,
} from "@/features/student/hooks/use-student-timetable";
import { cn } from "@/lib/utils";

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

const VIEW_SUBTITLE: Record<TimetableViewKey, string> = {
  day: "Choose Day, Week or Month",
  week: "Days across, time slots down",
  month: "Monthly calendar view",
  laboratory: "Laboratory sessions",
};

export function TimetableScheduleScreen() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const view = parseTimetableView(searchParams.get("view"));
  const anchorDate = searchParams.get("date")?.trim() || todayIso();
  const courseCode = searchParams.get("course")?.trim() || "";
  const slotParam = searchParams.get("slot")?.trim() || undefined;

  const dailyQuery = useTimetableDailyPage({
    anchorDate,
    courseCode: courseCode || undefined,
    slotId: slotParam,
    enabled: view === "day",
  });

  const weeklyQuery = useTimetableWeeklyPage({
    anchorDate,
    courseCode: courseCode || undefined,
    enabled: view === "week",
  });

  const monthlyQuery = useTimetableMonthlyPage(anchorDate, { enabled: view === "month" });
  /** Month + week session detail: daily slots for the URL anchor date (calendar day or week day). */
  const slotsForDetailDate = useTimetableDailyPage({
    anchorDate,
    courseCode: courseCode || undefined,
    enabled: view === "month" || (view === "week" && Boolean(slotParam)),
  });
  const labQuery = useTimetableLaboratoryPage({
    anchorDate,
    courseCode: courseCode || undefined,
    slotId: slotParam,
    enabled: view === "laboratory",
  });

  const selectedSlotId = useMemo(() => {
    if (slotParam) return slotParam;
    if (view === "day" && dailyQuery.data?.timeline_rows[0]) {
      return dailyQuery.data.timeline_rows[0].slot_id;
    }
    if (view === "laboratory" && labQuery.data?.timeline_rows[0]) {
      return labQuery.data.timeline_rows[0].slot_id;
    }
    if (view === "month" && slotsForDetailDate.data?.timeline_rows[0]) {
      return slotsForDetailDate.data.timeline_rows[0].slot_id;
    }
    return null;
  }, [slotParam, view, dailyQuery.data, labQuery.data, slotsForDetailDate.data]);

  const detailQuery = useTimetableSessionDetail(selectedSlotId, anchorDate);

  const navigate = useCallback(
    (patch: {
      view?: TimetableViewKey;
      date?: string;
      course?: string;
      slot?: string | null;
    }) => {
      router.push(
        buildTimetableQueryPath(TIMETABLE_SCHEDULE_PATH, {
          view: patch.view ?? view,
          date: patch.date ?? anchorDate,
          course: patch.course !== undefined ? patch.course : courseCode || undefined,
          slot: patch.slot === null ? undefined : (patch.slot ?? selectedSlotId ?? undefined),
        }),
      );
    },
    [anchorDate, courseCode, router, selectedSlotId, view],
  );

  const activeQuery =
    view === "day"
      ? dailyQuery
      : view === "week"
        ? weeklyQuery
        : view === "month"
          ? monthlyQuery
          : labQuery;

  const pageTitle =
    view === "day"
      ? dailyQuery.data?.page_title ?? "Daily Timetable"
      : view === "week"
        ? weeklyQuery.data?.page_title ?? "Weekly Timetable"
        : view === "month"
          ? monthlyQuery.data?.page_title ?? "Monthly Calendar View"
          : labQuery.data?.page_title ?? "Laboratory Timetable";

  const pageSubtitle =
    view === "day"
      ? (dailyQuery.data?.page_subtitle ?? VIEW_SUBTITLE.day)
      : view === "week"
        ? (weeklyQuery.data?.page_subtitle ?? VIEW_SUBTITLE.week)
        : view === "month"
          ? (monthlyQuery.data?.page_subtitle ?? VIEW_SUBTITLE.month)
          : (labQuery.data?.page_subtitle ?? VIEW_SUBTITLE.laboratory);

  const figmaNode =
    view === "day"
      ? "164:14590"
      : view === "week"
        ? "164:15251"
        : view === "laboratory"
          ? "164:15884"
          : undefined;

  return (
    <div className="space-y-4" data-figma-page="ST 05">
      <StAcademicsPageBlock
        title={pageTitle}
        description={pageSubtitle}
        figmaNode={figmaNode}
        actions={<TimetableViewSegment />}
      >
        <QueryState
          isLoading={activeQuery.isLoading}
          isError={activeQuery.isError}
          error={activeQuery.error}
          onRetry={() => void activeQuery.refetch()}
        >
          <div className="flex flex-col gap-3" data-figma-frame="164:14917">
            {view === "day" && dailyQuery.data ? (
              <>
                <StAcademicsSectionCard
                  title="Schedule"
                  footer={
                    <span>
                      {dailyQuery.data.academic_year_label} · {dailyQuery.data.semester_label}
                    </span>
                  }
                >
                  <div className="space-y-3 px-3 py-2.5">
                    <TimetableDateNav
                      subtitle={dailyQuery.data.page_subtitle}
                      prevHref={buildTimetableQueryPath(TIMETABLE_SCHEDULE_PATH, {
                        view: "day",
                        date: dailyQuery.data.prev_date,
                        course: courseCode || undefined,
                        slot: selectedSlotId ?? undefined,
                      })}
                      nextHref={buildTimetableQueryPath(TIMETABLE_SCHEDULE_PATH, {
                        view: "day",
                        date: dailyQuery.data.next_date,
                        course: courseCode || undefined,
                        slot: selectedSlotId ?? undefined,
                      })}
                    />
                    <TimetableCourseFilter
                      options={dailyQuery.data.course_filter_options}
                      value={courseCode}
                      onChange={(c) => navigate({ course: c || undefined, slot: null })}
                    />
                  </div>
                </StAcademicsSectionCard>
                <TimetableDaySessionsTable
                  title="Today"
                  rows={dailyQuery.data.timeline_rows}
                  selectedSlotId={selectedSlotId}
                  onSelect={(id) => navigate({ slot: id })}
                  footer={dailyQuery.data.timeline_footer}
                />
              </>
            ) : null}

            {view === "week" && weeklyQuery.data ? (
              <>
                <StAcademicsSectionCard
                  title="Filters"
                  footer={
                    <span>
                      {weeklyQuery.data.academic_year_label} · {weeklyQuery.data.semester_label}
                    </span>
                  }
                >
                  <div className="px-3 py-2.5">
                    <TimetableCourseFilter
                      options={weeklyQuery.data.course_filter_options}
                      value={courseCode}
                      onChange={(c) => navigate({ course: c || undefined, slot: null })}
                    />
                  </div>
                </StAcademicsSectionCard>
                <TimetableWeeklyGrid
                  days={weeklyQuery.data.days}
                  selectedSlotId={selectedSlotId}
                  onSelect={(id, dayDate) => navigate({ date: dayDate, slot: id })}
                  footer={weeklyQuery.data.week_footer}
                />
              </>
            ) : null}

            {view === "month" && monthlyQuery.data ? (
              <StAcademicsSectionCard title="Month" footer={<span>{monthlyQuery.data.month_footer}</span>}>
                <MonthGrid
                  data={monthlyQuery.data}
                  selectedDate={anchorDate}
                  onPickDay={(date) => navigate({ view: "month", date, slot: null })}
                />
                {slotsForDetailDate.data && slotsForDetailDate.data.timeline_rows.length > 0 ? (
                  <div className="mt-3">
                    <TimetableDaySessionsTable
                      title={slotsForDetailDate.data.page_subtitle}
                      rows={slotsForDetailDate.data.timeline_rows}
                      selectedSlotId={selectedSlotId}
                      onSelect={(id) => navigate({ slot: id })}
                      footer={slotsForDetailDate.data.timeline_footer}
                    />
                  </div>
                ) : null}
              </StAcademicsSectionCard>
            ) : null}

            {view === "laboratory" && labQuery.data ? (
              <>
                <StAcademicsSectionCard title="Laboratory schedule">
                  <div className="space-y-3 px-3 py-2.5">
                    <TimetableDateNav
                      subtitle={labQuery.data.page_subtitle}
                      prevHref={buildTimetableQueryPath(TIMETABLE_SCHEDULE_PATH, {
                        view: "laboratory",
                        date: labQuery.data.prev_date,
                        course: courseCode || undefined,
                        slot: selectedSlotId ?? undefined,
                      })}
                      nextHref={buildTimetableQueryPath(TIMETABLE_SCHEDULE_PATH, {
                        view: "laboratory",
                        date: labQuery.data.next_date,
                        course: courseCode || undefined,
                        slot: selectedSlotId ?? undefined,
                      })}
                    />
                    <TimetableCourseFilter
                      options={labQuery.data.course_filter_options}
                      value={courseCode}
                      onChange={(c) => navigate({ course: c || undefined, slot: null })}
                    />
                  </div>
                </StAcademicsSectionCard>
                <TimetableDaySessionsTable
                  title="Lab sessions"
                  rows={labQuery.data.timeline_rows}
                  selectedSlotId={selectedSlotId}
                  onSelect={(id) => navigate({ slot: id })}
                  footer={labQuery.data.timeline_footer}
                />
              </>
            ) : null}
          </div>
        </QueryState>

        <TimetableClassSessionDetailsSection
          detail={detailQuery.data ?? null}
          isLoading={Boolean(selectedSlotId) && detailQuery.isLoading}
          isError={detailQuery.isError}
          onClearSelection={selectedSlotId ? () => navigate({ slot: null }) : undefined}
        />
      </StAcademicsPageBlock>
    </div>
  );
}

function MonthGrid({
  data,
  selectedDate,
  onPickDay,
}: {
  data: NonNullable<ReturnType<typeof useTimetableMonthlyPage>["data"]>;
  selectedDate: string;
  onPickDay: (date: string) => void;
}) {
  return (
    <div className="overflow-x-auto px-2 py-2">
      <div className="mb-1 grid grid-cols-7 gap-1 text-center text-[11px] font-medium uppercase text-[#6b7280]">
        {data.weekday_labels.map((label) => (
          <div key={label} className="py-1">
            {label}
          </div>
        ))}
      </div>
      {data.weeks.map((week, wi) => (
        <div key={wi} className="grid grid-cols-7 gap-1">
          {week.map((cell) => (
            <MonthCell
              key={cell.anchor_date}
              cell={cell}
              selected={cell.anchor_date === selectedDate}
              onPickDay={onPickDay}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

function MonthCell({
  cell,
  selected,
  onPickDay,
}: {
  cell: {
    anchor_date: string;
    in_month: boolean;
    day_number: number | null;
    session_count: number;
    is_today: boolean;
  };
  selected: boolean;
  onPickDay: (date: string) => void;
}) {
  if (!cell.in_month) {
    return <div className="min-h-[3.25rem] rounded-md bg-transparent" aria-hidden />;
  }
  return (
    <button
      type="button"
      onClick={() => onPickDay(cell.anchor_date)}
      className={cn(
        "flex min-h-[3.25rem] flex-col items-center justify-center rounded-md border px-1 py-1 text-center transition-colors",
        selected || cell.is_today
          ? "border-[#245dd8] bg-[#eff6ff]"
          : "border-[#e8ecf2] bg-white hover:border-[#c5d4f0] hover:bg-[#f8fafc]",
      )}
    >
      <span className="text-[13px] font-semibold text-[#172b45]">{cell.day_number}</span>
      {cell.session_count > 0 ? (
        <span className="mt-0.5 text-[10px] font-medium text-[#245dd8]">
          {cell.session_count === 1 ? "Classes" : `${cell.session_count} classes`}
        </span>
      ) : (
        <span className="mt-0.5 text-[10px] text-[#9ca3af]">—</span>
      )}
    </button>
  );
}