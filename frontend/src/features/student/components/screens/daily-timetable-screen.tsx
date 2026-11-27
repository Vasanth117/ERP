"use client";

import { useCallback, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { TimetableViewSegment } from "@/features/student/components/ui/timetable-view-segment";
import {
  TimetableCourseFilter,
  TimetableDateNav,
  TimetableSessionDetailPanel,
  TimetableSessionTimeline,
  buildTimetableQueryPath,
} from "@/features/student/components/timetable/timetable-view-ui";
import { StAcademicsPageBlock, StAcademicsSectionCard } from "@/features/student/components/ui/student-academics-figma-ui";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import { useTimetableDailyPage } from "@/features/student/hooks/use-student-timetable";

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

export function DailyTimetableScreen() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const anchorDate = searchParams.get("date")?.trim() || todayIso();
  const courseCode = searchParams.get("course")?.trim() || "";
  const slotParam = searchParams.get("slot")?.trim() || undefined;

  const query = useTimetableDailyPage({
    anchorDate,
    courseCode: courseCode || undefined,
    slotId: slotParam,
  });

  const selectedSlotId = useMemo(() => {
    if (slotParam) return slotParam;
    return query.data?.timeline_rows[0]?.slot_id ?? null;
  }, [slotParam, query.data?.timeline_rows]);

  const navigate = useCallback(
    (patch: { date?: string; course?: string; slot?: string | null }) => {
      const next = buildTimetableQueryPath("/student/timetable/daily", {
        date: patch.date ?? anchorDate,
        course: patch.course !== undefined ? patch.course : courseCode || undefined,
        slot: patch.slot === null ? undefined : (patch.slot ?? selectedSlotId ?? undefined),
      });
      router.push(next);
    },
    [anchorDate, courseCode, router, selectedSlotId],
  );

  return (
    <div className="space-y-4" data-figma-page="ST 05">
      <QueryState
        isLoading={query.isLoading}
        isError={query.isError}
        error={query.error}
        onRetry={() => void query.refetch()}
      >
        {query.data ? (
          <DailyTimetableContent
            data={query.data}
            selectedSlotId={selectedSlotId}
            courseCode={courseCode}
            onCourseChange={(c) => navigate({ course: c || undefined, slot: null })}
            onSelectSlot={(id) => navigate({ slot: id })}
            prevHref={buildTimetableQueryPath("/student/timetable/daily", {
              date: query.data.prev_date,
              course: courseCode || undefined,
              slot: selectedSlotId ?? undefined,
            })}
            nextHref={buildTimetableQueryPath("/student/timetable/daily", {
              date: query.data.next_date,
              course: courseCode || undefined,
              slot: selectedSlotId ?? undefined,
            })}
          />
        ) : null}
      </QueryState>
    </div>
  );
}

function DailyTimetableContent({
  data,
  selectedSlotId,
  courseCode,
  onCourseChange,
  onSelectSlot,
  prevHref,
  nextHref,
}: {
  data: NonNullable<ReturnType<typeof useTimetableDailyPage>["data"]>;
  selectedSlotId: string | null;
  courseCode: string;
  onCourseChange: (code: string) => void;
  onSelectSlot: (id: string) => void;
  prevHref: string;
  nextHref: string;
}) {
  const termHint = `${data.academic_year_label} · ${data.semester_label}`;

  return (
    <StAcademicsPageBlock
      title={data.page_title}
      description={data.page_subtitle}
      figmaNode="164:14590"
      actions={<TimetableViewSegment />}
    >
      <div className="flex flex-col gap-3" data-figma-frame="164:14917">
        <StAcademicsSectionCard title="Schedule" footer={<span>{termHint}</span>}>
          <div className="space-y-3 px-3 py-2.5">
            <TimetableDateNav subtitle={data.page_subtitle} prevHref={prevHref} nextHref={nextHref} />
            <TimetableCourseFilter
              options={data.course_filter_options}
              value={courseCode}
              onChange={onCourseChange}
            />
          </div>
        </StAcademicsSectionCard>

        <TimetableSessionTimeline
          rows={data.timeline_rows}
          selectedSlotId={selectedSlotId}
          onSelect={onSelectSlot}
          footer={data.timeline_footer}
        />
        <TimetableSessionDetailPanel detail={data.session_detail} />
      </div>
    </StAcademicsPageBlock>
  );
}