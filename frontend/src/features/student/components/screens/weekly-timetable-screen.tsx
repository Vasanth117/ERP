"use client";

import Link from "next/link";
import { useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { TimetableViewSegment } from "@/features/student/components/ui/timetable-view-segment";
import {
  TimetableCourseFilter,
  TimetableSessionTimeline,
  buildTimetableQueryPath,
} from "@/features/student/components/timetable/timetable-view-ui";
import { StAcademicsPageBlock, StAcademicsSectionCard } from "@/features/student/components/ui/student-academics-figma-ui";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import { useTimetableWeeklyPage } from "@/features/student/hooks/use-student-timetable";

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

export function WeeklyTimetableScreen() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const anchorDate = searchParams.get("date")?.trim() || todayIso();
  const courseCode = searchParams.get("course")?.trim() || "";

  const query = useTimetableWeeklyPage({
    anchorDate,
    courseCode: courseCode || undefined,
  });

  const onCourseChange = useCallback(
    (c: string) => {
      router.push(
        buildTimetableQueryPath("/student/timetable/weekly", {
          date: anchorDate,
          course: c || undefined,
        }),
      );
    },
    [anchorDate, router],
  );

  return (
    <div className="space-y-4" data-figma-page="ST 05" data-figma-frame="164:15251">
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
            figmaNode="164:15251"
            actions={<TimetableViewSegment />}
          >
            <div className="space-y-3">
              <StAcademicsSectionCard
                title="Filters"
                footer={<span>{`${query.data.academic_year_label} · ${query.data.semester_label}`}</span>}
              >
                <div className="px-3 py-2.5">
                  <TimetableCourseFilter
                    options={query.data.course_filter_options}
                    value={courseCode}
                    onChange={onCourseChange}
                  />
                </div>
              </StAcademicsSectionCard>

              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
                {query.data.days.map((day) => (
                  <div key={day.anchor_date} className="min-w-0">
                    <div className="mb-1.5 flex items-center justify-between gap-2 px-0.5">
                      <div>
                        <p className="text-[13px] font-semibold text-[#172b45]">{day.day_label}</p>
                        <p className="text-[11px] text-[#6b7280]">{day.short_label}</p>
                      </div>
                      <Link
                        href={buildTimetableQueryPath("/student/timetable/daily", { date: day.anchor_date })}
                        className="text-[12px] font-medium text-[#245dd8] hover:underline"
                      >
                        Day view
                      </Link>
                    </div>
                    {day.slots.length === 0 ? (
                      <p className="rounded-lg border border-dashed border-[#e8ecf2] px-3 py-6 text-center text-[12px] text-[#9ca3af]">
                        No sessions
                      </p>
                    ) : (
                      <TimetableSessionTimeline
                        rows={day.slots}
                        selectedSlotId={null}
                        onSelect={(id) =>
                          router.push(
                            buildTimetableQueryPath("/student/timetable/daily", {
                              date: day.anchor_date,
                              slot: id,
                            }),
                          )
                        }
                        footer={`${day.session_count} session${day.session_count === 1 ? "" : "s"}`}
                      />
                    )}
                  </div>
                ))}
              </div>
              <p className="text-[12px] text-[#6b7280]">{query.data.week_footer}</p>
            </div>
          </StAcademicsPageBlock>
        ) : null}
      </QueryState>
    </div>
  );
}