"use client";

import {
  StAcademicsOutcomeBadge,
  StAcademicsPageBlock,
  StAcademicsSectionCard,
} from "@/features/student/components/ui/student-academics-figma-ui";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import { useRegistrationStatusPage } from "@/features/student/hooks/use-student-registration";
import type {
  RegistrationApprovalStep,
  RegistrationStatusPage,
} from "@/features/student/types/registration";
import { cn } from "@/lib/utils";

export function RegistrationStatusScreen() {
  const pageQuery = useRegistrationStatusPage();

  return (
    <QueryState
      isLoading={pageQuery.isLoading}
      isError={pageQuery.isError}
      error={pageQuery.error}
      onRetry={() => void pageQuery.refetch()}
    >
      {pageQuery.data ? <RegistrationStatusContent data={pageQuery.data} /> : null}
    </QueryState>
  );
}

function RegistrationStatusContent({ data }: { data: RegistrationStatusPage }) {
  const { status, history } = data;

  return (
    <div className="flex flex-col gap-3">
      <StAcademicsPageBlock
        title={status.page_title}
        description={status.page_subtitle}
        figmaNode="164:13326"
        compact
      >
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_240px]">
          <StAcademicsSectionCard title="Courses" footer={<span>{status.courses_footer_label}</span>}>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[13px]">
                <thead>
                  <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
                    <th className="px-4 py-2 font-medium">Code</th>
                    <th className="px-4 py-2 font-medium">Course</th>
                    <th className="px-4 py-2 text-right font-medium">Credits</th>
                    <th className="px-4 py-2 text-right font-medium">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#e8ecf2]">
                  {status.courses.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-4 py-6 text-center text-[13px] text-[#6b7280]">
                        No courses in your current registration.
                      </td>
                    </tr>
                  ) : (
                    status.courses.map((row) => (
                      <tr key={row.course_code} className="text-[#172b45]">
                        <td className="px-4 py-2 font-semibold tabular-nums">{row.course_code}</td>
                        <td className="px-4 py-2">{row.course_name}</td>
                        <td className="px-4 py-2 text-right tabular-nums">{row.credit_units}</td>
                        <td className="px-4 py-2 text-right">
                          <StAcademicsOutcomeBadge label={row.status_label} tone={row.status_tone} />
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </StAcademicsSectionCard>

          <StAcademicsSectionCard title="Approval">
            <RegistrationApprovalTimeline steps={status.approval_steps} />
          </StAcademicsSectionCard>
        </div>
      </StAcademicsPageBlock>

      <section className="scroll-mt-4 border-t border-[#e8ecf2] pt-3">
        <StAcademicsPageBlock
          title={history.page_title}
          description={history.page_subtitle}
          figmaNode="164:13653"
          compact
        >
          <StAcademicsSectionCard title="History" footer={<span>{history.footer_label}</span>}>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-[13px]">
                <thead>
                  <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
                    <th className="px-4 py-2 font-medium">Reference</th>
                    <th className="px-4 py-2 font-medium">Semester</th>
                    <th className="px-4 py-2 font-medium">Courses</th>
                    <th className="px-4 py-2 font-medium">Credits</th>
                    <th className="px-4 py-2 font-medium">Submitted</th>
                    <th className="px-4 py-2 text-right font-medium">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#e8ecf2]">
                  {history.rows.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-4 py-6 text-center text-[13px] text-[#6b7280]">
                        No earlier semester registrations yet.
                      </td>
                    </tr>
                  ) : (
                    history.rows.map((row) => (
                      <tr key={row.reference_label} className="text-[#172b45]">
                        <td className="px-4 py-2 font-semibold tabular-nums">{row.reference_label}</td>
                        <td className="px-4 py-2 text-[#6b7280]">{row.semester_label}</td>
                        <td className="px-4 py-2 tabular-nums">{row.course_count}</td>
                        <td className="px-4 py-2 tabular-nums">{row.credit_units}</td>
                        <td className="px-4 py-2 text-[#6b7280]">{row.submitted_at_label}</td>
                        <td className="px-4 py-2 text-right">
                          <StAcademicsOutcomeBadge label={row.status_label} tone={row.status_tone} />
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </StAcademicsSectionCard>
        </StAcademicsPageBlock>
      </section>
    </div>
  );
}

function RegistrationApprovalTimeline({ steps }: { steps: RegistrationApprovalStep[] }) {
  return (
    <ol className="px-4 py-2.5">
      {steps.map((step, idx) => {
        const isLast = idx === steps.length - 1;
        const completed = step.state === "completed";
        const current = step.state === "current";
        const dotClass = cn(
          "mt-0.5 size-2.5 shrink-0 rounded-full ring-2 ring-white",
          completed && "bg-[#1f7a45]",
          current && "bg-[#b45309]",
          !completed && !current && "bg-[#cbd5e1]",
        );
        const lineClass = completed && !isLast ? "bg-[#1f7a45]" : "bg-[#e2e8f0]";
        const detailClass = cn(
          "text-[12px]",
          completed && "font-medium text-[#1f7a45]",
          current && "font-medium text-[#b45309]",
          step.tone === "warning" && !completed && "text-[#b45309]",
          !completed && !current && step.tone !== "warning" && "text-[#9ca3af]",
        );
        return (
          <li key={step.key} className="flex gap-3">
            <div className="flex w-2.5 flex-col items-center">
              <span className={dotClass} aria-hidden />
              {!isLast ? <span className={cn("my-0.5 w-0.5 min-h-[1.35rem] flex-1 rounded-full", lineClass)} aria-hidden /> : null}
            </div>
            <div className={cn("min-w-0 pb-3", isLast && "pb-0")}>
              <p className={cn("text-[13px] font-medium", completed || current ? "text-[#172b45]" : "text-[#6b7280]")}>
                {step.label}
              </p>
              <p className={detailClass}>{step.detail}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}