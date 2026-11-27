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
import { useTimetableLaboratoryPage } from "@/features/student/hooks/use-student-timetable";

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

export function LaboratoryTimetableScreen() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const anchorDate = searchParams.get("date")?.trim() || todayIso();
  const courseCode = searchParams.get("course")?.trim() || "";
  const slotParam = searchParams.get("slot")?.trim() || undefined;

  const query = useTimetableLaboratoryPage({
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
      router.push(
        buildTimetableQueryPath("/student/timetable/laboratory", {
          date: patch.date ?? anchorDate,
          course: patch.course !== undefined ? patch.course : courseCode || undefined,
          slot: patch.slot === null ? undefined : (patch.slot ?? selectedSlotId ?? undefined),
        }),
      );
    },
    [anchorDate, courseCode, router, selectedSlotId],
  );

  return (
    <div className="space-y-4" data-figma-page="ST 05" data-figma-frame="164:15884">
      <QueryState
        isLoading={query.isLoading}
        isError={query.isError}
        error={query.error}
        onRetry={() => void query.refetch()}
      >
        {query.data ? (
          <StAcademicsPageBlock
            title={query.data.page_title}
            description={query.data.page_subtitle}
            figmaNode="164:15884"
            actions={<TimetableViewSegment />}
          >
            <div className="flex flex-col gap-3">
              <StAcademicsSectionCard title="Laboratory schedule">
                <div className="space-y-3 px-3 py-2.5">
                  <TimetableDateNav
                    subtitle={query.data.page_subtitle}
                    prevHref={buildTimetableQueryPath("/student/timetable/laboratory", {
                      date: query.data.prev_date,
                      course: courseCode || undefined,
                      slot: selectedSlotId ?? undefined,
                    })}
                    nextHref={buildTimetableQueryPath("/student/timetable/laboratory", {
                      date: query.data.next_date,
                      course: courseCode || undefined,
                      slot: selectedSlotId ?? undefined,
                    })}
                  />
                  <TimetableCourseFilter
                    options={query.data.course_filter_options}
                    value={courseCode}
                    onChange={(c) => navigate({ course: c || undefined, slot: null })}
                  />
                </div>
              </StAcademicsSectionCard>

              <TimetableSessionTimeline
                rows={query.data.timeline_rows}
                selectedSlotId={selectedSlotId}
                onSelect={(id) => navigate({ slot: id })}
                footer={query.data.timeline_footer}
              />
              <TimetableSessionDetailPanel detail={query.data.session_detail} />
            </div>
          </StAcademicsPageBlock>
        ) : null}
      </QueryState>
    </div>
  );
}