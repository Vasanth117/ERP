"use client";

import Link from "next/link";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { MailIcon } from "@/components/icons/erp/generated/mail";
import { TriangleAlertIcon } from "@/components/icons/erp/generated/triangle-alert";
import {
  CollegeAdminDashboardKpiCard,
  CollegeAdminKpiGrid,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import {
  StAcademicsDetailField,
  StAcademicsOutcomeBadge,
  StAcademicsPageBlock,
  StAcademicsSectionCard,
  displayOrDash,
} from "@/features/student/components/ui/student-academics-figma-ui";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import { PORTAL_CARD, STUDENT_BTN_PRIMARY } from "@/features/student/components/ui/student-portal-tokens";
import { useRegistrationOverview } from "@/features/student/hooks/use-student-registration";
import type {
  RegistrationClosedPanel,
  RegistrationOverviewPage,
} from "@/features/student/types/registration";
import { cn } from "@/lib/utils";

export function RegistrationOverviewScreen() {
  const { data, isLoading, isError, error, refetch } = useRegistrationOverview();

  return (
    <QueryState
      isLoading={isLoading}
      isError={isError}
      error={error}
      onRetry={() => void refetch()}
    >
      {data ? (
        <div className="flex flex-col gap-0">
          <RegistrationDashboardBlock data={data} />
          {data.closed_panel ? (
            <RegistrationClosedBlock
              panel={data.closed_panel}
              contactHref={data.contact_department_href}
            />
          ) : null}
        </div>
      ) : null}
    </QueryState>
  );
}

function RegistrationDashboardBlock({ data }: { data: RegistrationOverviewPage }) {
  const { kpis, steps } = data;

  return (
    <StAcademicsPageBlock
      title={data.page_title}
      description={data.page_subtitle}
      figmaNode="164:10577"
      actions={
        data.show_start_registration ? (
          <Link href={data.start_registration_href} className={STUDENT_BTN_PRIMARY}>
            <span>Start registration</span>
            <ChevronRightIcon className="size-3.5 stroke-[2]" aria-hidden />
          </Link>
        ) : (
          <Link href={data.contact_department_href} className={STUDENT_BTN_PRIMARY}>
            <MailIcon className="size-3.5 stroke-[2]" aria-hidden />
            <span>Contact department</span>
          </Link>
        )
      }
    >
      <section aria-label="Registration progress" className={cn(PORTAL_CARD, "overflow-x-auto px-4 py-3")}>
        <div className="flex min-w-[640px] items-center justify-between gap-1">
          {steps.map((step, idx) => {
            const isLast = idx === steps.length - 1;
            const completed = step.state === "completed";
            const current = step.state === "current";
            return (
              <div key={step.key} className="flex flex-1 items-center last:flex-none">
                <div className="flex min-w-0 items-center gap-1.5">
                  {completed ? (
                    <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-[#2563eb] text-white">
                      <CheckIcon className="size-3 stroke-[2.5]" aria-hidden />
                    </span>
                  ) : current ? (
                    <span className="flex size-5 shrink-0 items-center justify-center rounded-full border-2 border-[#2563eb] bg-white text-[10px] font-bold text-[#2563eb]">
                      {idx + 1}
                    </span>
                  ) : (
                    <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-[#f1f5f9] text-[10px] font-medium text-[#9ca3af]">
                      {idx + 1}
                    </span>
                  )}
                  <span
                    className={cn(
                      "truncate text-[11px] font-medium",
                      current ? "font-semibold text-[#111827]" : completed ? "text-[#111827]" : "text-[#9ca3af]",
                    )}
                  >
                    {step.label}
                  </span>
                </div>
                {!isLast ? (
                  <div
                    className={cn(
                      "mx-1.5 h-px min-w-[0.75rem] flex-1",
                      completed || current ? "bg-[#2563eb]" : "bg-[#e2e8f0]",
                    )}
                    aria-hidden
                  />
                ) : null}
              </div>
            );
          })}
        </div>
      </section>

      <CollegeAdminKpiGrid className="grid-cols-2 gap-3 lg:grid-cols-4">
        <CollegeAdminDashboardKpiCard
          label="Window"
          value={displayOrDash(kpis.window_label)}
          hint={kpis.window_hint ?? undefined}
          index={0}
          kpiKey="st04-window"
        />
        <CollegeAdminDashboardKpiCard
          label="Credit limit"
          value={displayOrDash(kpis.credit_limit_label)}
          index={1}
          kpiKey="st04-credit-limit"
        />
        <CollegeAdminDashboardKpiCard
          label="Selected"
          value={displayOrDash(kpis.selected_count)}
          index={2}
          kpiKey="st04-selected"
        />
        <CollegeAdminDashboardKpiCard
          label="Status"
          value={displayOrDash(kpis.status_label)}
          index={3}
          kpiKey="st04-status"
        />
      </CollegeAdminKpiGrid>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_280px]">
        <StAcademicsSectionCard title="Available courses" footer={<span>{data.courses_footer_label}</span>}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-[13px]">
              <thead>
                <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
                  <th className="px-4 py-2.5 font-medium">Code</th>
                  <th className="px-4 py-2.5 font-medium">Course</th>
                  <th className="px-4 py-2.5 font-medium">Category</th>
                  <th className="px-4 py-2.5 font-medium">Credits</th>
                  <th className="px-4 py-2.5 font-medium">Prerequisite</th>
                  <th className="px-4 py-2.5 font-medium">Seats</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e8ecf2]">
                {data.available_courses.map((row) => (
                  <tr key={row.course_code} className="text-[#172b45]">
                    <td className="px-4 py-2.5 font-semibold tabular-nums">{row.course_code}</td>
                    <td className="px-4 py-2.5">{row.course_name}</td>
                    <td className="px-4 py-2.5 text-[#6b7280]">{row.category_label}</td>
                    <td className="px-4 py-2.5 tabular-nums">{row.credit_units}</td>
                    <td className="px-4 py-2.5 tabular-nums text-[#6b7280]">{row.prerequisite_label}</td>
                    <td className="px-4 py-2.5 text-[#6b7280]">{row.seats_label}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </StAcademicsSectionCard>

        <StAcademicsSectionCard title="Before you register">
          <ul className="divide-y divide-[#e8ecf2]">
            {data.prerequisite_checks.map((item) => (
              <li key={item.key} className="flex items-start justify-between gap-3 px-4 py-3">
                <div className="min-w-0">
                  <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
                  <p className="mt-0.5 text-[12px] text-[#6b7280]">{item.detail}</p>
                </div>
                <StAcademicsOutcomeBadge label={item.status_label} tone={item.status_tone} />
              </li>
            ))}
          </ul>
        </StAcademicsSectionCard>
      </div>
    </StAcademicsPageBlock>
  );
}

function RegistrationClosedBlock({
  panel,
  contactHref,
}: {
  panel: RegistrationClosedPanel;
  contactHref: string;
}) {
  return (
    <section
      id="st-04-11-registration-closed"
      className="scroll-mt-4 border-t border-[#e8ecf2] pt-4"
      aria-label="Registration period closed screen"
    >
      <StAcademicsPageBlock
        title={panel.page_title}
        description={panel.page_subtitle}
        figmaNode="164:13961"
        actions={
          <Link href={contactHref} className={STUDENT_BTN_PRIMARY}>
            <MailIcon className="size-3.5 stroke-[2]" aria-hidden />
            <span>Contact department</span>
          </Link>
        }
      >
        {panel.show_late_registration_banner ? (
          <div className="flex flex-col gap-2 rounded border border-[#fde68a] bg-[#fffbeb] px-4 py-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex gap-3">
              <TriangleAlertIcon className="mt-0.5 size-4 shrink-0 text-[#d97706]" aria-hidden />
              <div className="min-w-0">
                <p className="text-[13px] font-semibold text-[#92400e]">{panel.banner_title}</p>
                <p className="mt-1 text-[12px] leading-snug text-[#a16207]">{panel.banner_body}</p>
              </div>
            </div>
            {panel.show_raise_request_action ? (
              <Link
                href={panel.raise_request_href}
                className="shrink-0 pt-0.5 text-[13px] font-semibold text-[#245dd8] hover:underline"
              >
                Raise a request →
              </Link>
            ) : null}
          </div>
        ) : null}

        <StAcademicsSectionCard title="Window" className="mt-0">
          <div className="px-5 py-3">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <StAcademicsDetailField label="Opened" value={panel.window_opened_label} />
              <StAcademicsDetailField label="Closed" value={panel.window_closed_label} />
            </div>
            <div className="mt-4 border-t border-[#e8ecf2] pt-3">
              <StAcademicsDetailField label="Your status" value={panel.student_status_label} />
            </div>
          </div>
        </StAcademicsSectionCard>
      </StAcademicsPageBlock>
    </section>
  );
}