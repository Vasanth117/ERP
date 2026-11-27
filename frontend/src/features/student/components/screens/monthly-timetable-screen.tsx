"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { TimetableViewSegment } from "@/features/student/components/ui/timetable-view-segment";
import { buildTimetableQueryPath } from "@/features/student/components/timetable/timetable-view-ui";
import { StAcademicsPageBlock, StAcademicsSectionCard } from "@/features/student/components/ui/student-academics-figma-ui";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import { useTimetableMonthlyPage } from "@/features/student/hooks/use-student-timetable";
import { cn } from "@/lib/utils";

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

export function MonthlyTimetableScreen() {
  const searchParams = useSearchParams();
  const anchorDate = searchParams.get("date")?.trim() || todayIso();
  const query = useTimetableMonthlyPage(anchorDate);

  return (
    <div className="space-y-4" data-figma-page="ST 05">
      <QueryState
        isLoading={query.isLoading}
        isError={query.isError}
        error={query.error}
        onRetry={() => void query.refetch()}
      >
        {query.data ? <MonthlyContent data={query.data} /> : null}
      </QueryState>
    </div>
  );
}

function MonthlyContent({
  data,
}: {
  data: NonNullable<ReturnType<typeof useTimetableMonthlyPage>["data"]>;
}) {
  return (
    <StAcademicsPageBlock
      title={data.page_title}
      description={data.page_subtitle}
      actions={<TimetableViewSegment />}
    >
      <StAcademicsSectionCard title="Month" footer={<span>{data.month_footer}</span>}>
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
                <MonthCell key={cell.anchor_date} cell={cell} />
              ))}
            </div>
          ))}
        </div>
      </StAcademicsSectionCard>
      <p className="text-[12px] text-[#6b7280]">
        {data.academic_year_label} · {data.semester_label}
      </p>
    </StAcademicsPageBlock>
  );
}

function MonthCell({
  cell,
}: {
  cell: {
    anchor_date: string;
    in_month: boolean;
    day_number: number | null;
    session_count: number;
    is_today: boolean;
  };
}) {
  if (!cell.in_month) {
    return <div className="min-h-[3.25rem] rounded-md bg-transparent" aria-hidden />;
  }
  const href = buildTimetableQueryPath("/student/timetable/daily", { date: cell.anchor_date });
  return (
    <Link
      href={href}
      className={cn(
        "flex min-h-[3.25rem] flex-col items-center justify-center rounded-md border px-1 py-1 text-center transition-colors",
        cell.is_today
          ? "border-[#245dd8] bg-[#eff6ff]"
          : "border-[#e8ecf2] bg-white hover:border-[#c5d4f0] hover:bg-[#f8fafc]",
      )}
    >
      <span className="text-[13px] font-semibold text-[#172b45]">{cell.day_number}</span>
      {cell.session_count > 0 ? (
        <span className="mt-0.5 text-[10px] font-medium text-[#245dd8]">
          {cell.session_count} class{cell.session_count === 1 ? "" : "es"}
        </span>
      ) : (
        <span className="mt-0.5 text-[10px] text-[#9ca3af]">—</span>
      )}
    </Link>
  );
}