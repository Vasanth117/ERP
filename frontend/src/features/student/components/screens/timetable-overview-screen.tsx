"use client";

import Link from "next/link";

import { CalendarDaysIcon } from "@/components/icons/erp/generated/calendar-days";
import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { RefreshCwIcon } from "@/components/icons/erp/generated/refresh-cw";
import {
  CollegeAdminDashboardKpiCard,
  CollegeAdminKpiGrid,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import {
  StAcademicsOutcomeBadge,
  StAcademicsPageBlock,
  StAcademicsSectionCard,
  displayOrDash,
} from "@/features/student/components/ui/student-academics-figma-ui";
import { QueryState, formatTime } from "@/features/student/components/ui/student-screen-ui";
import { STUDENT_BTN_PRIMARY } from "@/features/student/components/ui/student-portal-tokens";
import { useTimetableOverview } from "@/features/student/hooks/use-student-timetable";
import type {
  TimetableOverviewHighlight,
  TimetableOverviewPage,
} from "@/features/student/types/timetable";

function formatOverviewSubtitle(anchorDate: string, weekNumber: number): string {
  const d = new Date(`${anchorDate}T12:00:00`);
  const weekday = d.toLocaleDateString(undefined, { weekday: "long" });
  const datePart = d.toLocaleDateString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
  return `${weekday} ${datePart} · Week ${weekNumber}`;
}

export function TimetableOverviewScreen() {
  const { data, isLoading, isError, error, refetch } = useTimetableOverview();

  return (
    <div className="space-y-6" data-figma-page="ST 05" data-figma-frame="164:14234">
      <QueryState
        isLoading={isLoading}
        isError={isError}
        error={error}
        onRetry={() => void refetch()}
      >
        {data ? <TimetableOverviewContent data={data} /> : null}
      </QueryState>
    </div>
  );
}

function TimetableOverviewContent({ data }: { data: TimetableOverviewPage }) {
  const { kpis } = data;
  const subtitle = formatOverviewSubtitle(data.anchor_date, data.iso_week_number);

  return (
    <StAcademicsPageBlock
      title={data.page_title}
      description={subtitle}
      figmaNode="164:14234"
      actions={
        <Link href="/student/timetable/schedule?view=week" className={STUDENT_BTN_PRIMARY}>
          <span>Weekly view</span>
          <ChevronRightIcon className="size-3.5 stroke-[2]" aria-hidden />
        </Link>
      }
    >
      <CollegeAdminKpiGrid className="grid-cols-2 gap-3 lg:grid-cols-4">
        <CollegeAdminDashboardKpiCard
          label="Classes today"
          value={String(kpis.classes_today)}
          index={0}
          kpiKey="st05-classes-today"
        />
        <CollegeAdminDashboardKpiCard
          label="This week"
          value={String(kpis.classes_this_week)}
          index={1}
          kpiKey="st05-classes-week"
        />
        <CollegeAdminDashboardKpiCard
          label="Next exam"
          value={displayOrDash(kpis.next_exam_label)}
          hint={kpis.next_exam_hint ?? undefined}
          index={2}
          kpiKey="st05-next-exam"
        />
        <CollegeAdminDashboardKpiCard
          label="Changes"
          value={String(kpis.changes_count)}
          hint={kpis.changes_hint ?? undefined}
          hintTone={kpis.changes_hint ? "warning" : undefined}
          index={3}
          kpiKey="st05-changes"
        />
      </CollegeAdminKpiGrid>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(260px,320px)]">
        <StAcademicsSectionCard title="Today" footer={<span>{data.today_sessions_footer}</span>}>
          {data.today_rows.length === 0 ? (
            <p className="px-4 py-8 text-center text-[13px] text-[#9ca3af]">
              No classes scheduled for this day.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-[13px]">
                <thead>
                  <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
                    <th className="px-4 py-2.5 font-medium">Time</th>
                    <th className="px-4 py-2.5 font-medium">Subject</th>
                    <th className="px-4 py-2.5 font-medium">Type</th>
                    <th className="px-4 py-2.5 font-medium">Room</th>
                    <th className="px-4 py-2.5 font-medium">Faculty</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#e8ecf2]">
                  {data.today_rows.map((row) => (
                    <tr key={row.id} className="text-[#172b45]">
                      <td className="px-4 py-2.5 whitespace-nowrap tabular-nums">
                        {formatTime(row.start_time)} – {formatTime(row.end_time)}
                      </td>
                      <td className="px-4 py-2.5 font-medium">{row.subject_label}</td>
                      <td className="px-4 py-2.5 text-[#6b7280]">{row.session_type_label}</td>
                      <td className="px-4 py-2.5 text-[#6b7280]">{row.room_label}</td>
                      <td className="px-4 py-2.5 text-[#6b7280]">{row.faculty_label}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </StAcademicsSectionCard>

        <StAcademicsSectionCard title="Highlights">
          {data.highlights.length === 0 ? (
            <p className="px-4 py-8 text-center text-[13px] text-[#9ca3af]">
              No recent timetable updates or holidays.
            </p>
          ) : (
            <ul className="divide-y divide-[#e8ecf2]">
              {data.highlights.map((item) => (
                <HighlightRow key={`${item.kind}-${item.id}`} item={item} />
              ))}
            </ul>
          )}
        </StAcademicsSectionCard>
      </div>
    </StAcademicsPageBlock>
  );
}

function HighlightRow({ item }: { item: TimetableOverviewHighlight }) {
  const Icon = item.kind === "change" ? RefreshCwIcon : CalendarDaysIcon;
  return (
    <li className="flex gap-3 px-4 py-3">
      <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg bg-[#f3f4f6] text-[#6b7280]">
        <Icon className="size-4 stroke-[1.75]" aria-hidden />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
        {item.subtitle ? (
          <p className="mt-0.5 text-[12px] text-[#6b7280]">{item.subtitle}</p>
        ) : null}
      </div>
      <StAcademicsOutcomeBadge label={item.badge_label} tone={item.badge_tone} />
    </li>
  );
}