"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { DownloadIcon } from "@/components/icons/erp/generated/download";
import { SendIcon } from "@/components/icons/erp/generated/send";
import { TriangleAlertIcon } from "@/components/icons/erp/generated/triangle-alert";
import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import {
  StAcademicsDetailField,
  StAcademicsOutcomeBadge,
  StAcademicsPageBlock,
  StAcademicsSectionCard,
  StAcademicsToggle,
} from "@/features/student/components/ui/student-academics-figma-ui";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import { PORTAL_CARD, STUDENT_BTN_OUTLINE, STUDENT_BTN_PRIMARY } from "@/features/student/components/ui/student-portal-tokens";
import {
  useRegistrationReviewPage,
  useSubmitRegistration,
} from "@/features/student/hooks/use-student-registration";
import type {
  RegistrationOverviewStep,
  RegistrationReviewPage,
  RegistrationSelectionInput,
} from "@/features/student/types/registration";
import { cn } from "@/lib/utils";

type ReviewSubPanel = "confirmation" | "validation";

export function RegistrationReviewScreen() {
  const { data, isLoading, isError, error, refetch } = useRegistrationReviewPage();

  return (
    <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
      {data ? <RegistrationReviewContent data={data} onRefresh={() => void refetch()} /> : null}
    </QueryState>
  );
}

function RegistrationReviewContent({
  data,
  onRefresh,
}: {
  data: RegistrationReviewPage;
  onRefresh: () => void;
}) {
  const submit = useSubmitRegistration();
  const [subPanel, setSubPanel] = useState<ReviewSubPanel>(data.default_sub_panel);
  const [declaration, setDeclaration] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    setSubPanel(data.default_sub_panel);
  }, [data.default_sub_panel, data.confirmation.is_submitted]);

  const selections: RegistrationSelectionInput[] = data.summary.selected_rows.map((row) => ({
    course_id: row.course_id,
    course_code: row.course_code,
    registration_type: row.registration_type,
    elective_group_id: row.elective_group_id,
  }));

  const onSubmit = () => {
    setSubmitError(null);
    if (!declaration) {
      setSubmitError("Accept the declaration before submitting.");
      return;
    }
    if (!data.summary.submit_enabled) {
      setSubPanel("validation");
      setSubmitError("Fix validation issues before submitting.");
      return;
    }
    submit.mutate(selections, {
      onSuccess: () => {
        onRefresh();
        setSubPanel("confirmation");
      },
      onError: (err) => {
        setSubmitError(err instanceof Error ? err.message : "Submit failed");
        setSubPanel("validation");
      },
    });
  };

  const { summary } = data;

  return (
    <div className="flex flex-col gap-3">
      <StAcademicsPageBlock
        title={summary.page_title}
        description={summary.page_subtitle}
        figmaNode="164:12282"
        compact
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Link href={summary.back_href} className={STUDENT_BTN_OUTLINE}>
              <ChevronLeftIcon className="size-3.5 stroke-[2]" aria-hidden />
              <span>Back</span>
            </Link>
            <button
              type="button"
              disabled={submit.isPending || !declaration}
              onClick={onSubmit}
              className={cn(STUDENT_BTN_PRIMARY, (submit.isPending || !declaration) && "pointer-events-none opacity-70")}
            >
              <SendIcon className="size-3.5 stroke-[2]" aria-hidden />
              <span>Submit registration</span>
            </button>
          </div>
        }
      >
        {submitError ? (
          <p className="text-[12px] font-medium text-[#c2410c]" role="alert">
            {submitError}
          </p>
        ) : null}

        <RegistrationFlowStepper steps={summary.steps} />

        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_220px]">
          <StAcademicsSectionCard title="Selected" footer={<span>{summary.footer_label}</span>}>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[13px]">
                <thead>
                  <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
                    <th className="px-4 py-2 font-medium">Code</th>
                    <th className="px-4 py-2 font-medium">Course</th>
                    <th className="px-4 py-2 font-medium">Category</th>
                    <th className="px-4 py-2 text-right font-medium">Credits</th>
                  </tr>
                </thead>
                    <tbody className="divide-y divide-[#e8ecf2]">
                      {summary.selected_rows.length === 0 ? (
                        <tr>
                          <td colSpan={4} className="px-4 py-6 text-center text-[13px] text-[#6b7280]">
                            No courses in your draft yet. Save selections from Elective or Course, or reload after
                            bootstrap seeds data.
                          </td>
                        </tr>
                      ) : (
                        summary.selected_rows.map((row) => (
                          <tr key={row.course_id} className="text-[#172b45]">
                            <td className="px-4 py-2 font-semibold tabular-nums">{row.course_code}</td>
                            <td className="px-4 py-2">{row.course_name}</td>
                            <td className="px-4 py-2 text-[#6b7280]">{row.category_label}</td>
                            <td className="px-4 py-2 text-right tabular-nums">{row.credit_units}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
              </table>
            </div>
          </StAcademicsSectionCard>

          <div className="space-y-3">
            <StAcademicsSectionCard title="Totals">
              <ul className="divide-y divide-[#e8ecf2] text-[13px]">
                <li className="flex justify-between gap-3 px-4 py-2.5">
                  <span className="text-[#6b7280]">Courses</span>
                  <span className="font-semibold text-[#111827]">{summary.totals.course_count}</span>
                </li>
                <li className="flex justify-between gap-3 px-4 py-2.5">
                  <span className="text-[#6b7280]">Credits</span>
                  <span className="font-semibold text-[#111827]">{summary.totals.credit_units}</span>
                </li>
                <li className="flex justify-between gap-3 px-4 py-2.5">
                  <span className="text-[#6b7280]">Fees</span>
                  <span className="font-medium text-[#111827]">{summary.totals.fees_label}</span>
                </li>
              </ul>
            </StAcademicsSectionCard>

            <StAcademicsSectionCard title="Declaration">
              <div className="flex items-center justify-between gap-3 px-4 py-2.5">
                <span className="text-[12px] text-[#374151]">{summary.declaration_label}</span>
                <StAcademicsToggle
                  checked={declaration}
                  onChange={setDeclaration}
                  ariaLabel={summary.declaration_label}
                />
              </div>
            </StAcademicsSectionCard>
          </div>
        </div>
      </StAcademicsPageBlock>

      <section className="scroll-mt-4 border-t border-[#e8ecf2] pt-3">
        <ReviewSubTabs value={subPanel} onChange={setSubPanel} />
        {subPanel === "confirmation" ? (
          <ConfirmationPanel section={data.confirmation} />
        ) : (
          <ValidationPanel section={data.validation} />
        )}
      </section>
    </div>
  );
}

function ReviewSubTabs({
  value,
  onChange,
}: {
  value: ReviewSubPanel;
  onChange: (v: ReviewSubPanel) => void;
}) {
  const tabs: { key: ReviewSubPanel; label: string }[] = [
    { key: "confirmation", label: "Confirmation" },
    { key: "validation", label: "Validation" },
  ];
  return (
    <div
      className="mb-3 grid grid-cols-2 gap-1.5 rounded-lg border border-[#e3e9f2] bg-[#f8fafc] p-1"
      role="tablist"
      aria-label="Review outcome panels"
    >
      {tabs.map((tab) => (
        <button
          key={tab.key}
          type="button"
          role="tab"
          aria-selected={value === tab.key}
          onClick={() => onChange(tab.key)}
          className={cn(
            "rounded-md py-2 text-[14px] font-medium transition-all",
            value === tab.key
              ? "border border-[#e3e9f2] bg-white text-[#245dd8] shadow-sm"
              : "border border-transparent text-[#64748b] hover:text-[#172b45]",
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

function ValidationPanel({ section }: { section: RegistrationReviewPage["validation"] }) {
  return (
    <StAcademicsPageBlock
      title={section.page_title}
      description={section.page_subtitle}
      figmaNode="164:12663"
      compact
      actions={
        <Link href={section.fix_selection_href} className={STUDENT_BTN_OUTLINE}>
          <ChevronLeftIcon className="size-3.5 stroke-[2]" aria-hidden />
          <span>Fix selection</span>
        </Link>
      }
    >
      <RegistrationFlowStepper steps={section.steps} />

      {section.alert_title ? (
        <div
          className={cn(PORTAL_CARD, "flex gap-3 border-[#fecaca] bg-[#fef2f2] px-4 py-3")}
          role="alert"
        >
          <TriangleAlertIcon className="size-4 shrink-0 text-[#dc2626]" aria-hidden />
          <div>
            <p className="text-[13px] font-semibold text-[#b91c1c]">{section.alert_title}</p>
            {section.alert_body ? (
              <p className="mt-0.5 text-[12px] text-[#991b1b]">{section.alert_body}</p>
            ) : null}
          </div>
        </div>
      ) : null}

      <StAcademicsSectionCard title="Validation" footer={<span>{section.checks_footer_label}</span>}>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[13px]">
            <thead>
              <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
                <th className="px-4 py-2 font-medium">Check</th>
                <th className="px-4 py-2 font-medium">Course</th>
                <th className="px-4 py-2 text-right font-medium">Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e8ecf2]">
              {section.checks.map((row) => (
                <tr key={`${row.check_key}-${row.course_label}`}>
                  <td className="px-4 py-2 text-[#111827]">{row.check_label}</td>
                  <td className="px-4 py-2 text-[#6b7280]">{row.course_label}</td>
                  <td className="px-4 py-2 text-right">
                    <StAcademicsOutcomeBadge label={row.result_label} tone={row.result_tone} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </StAcademicsSectionCard>
    </StAcademicsPageBlock>
  );
}

function ConfirmationPanel({ section }: { section: RegistrationReviewPage["confirmation"] }) {
  return (
    <StAcademicsPageBlock
      title={section.page_title}
      description={section.page_subtitle}
      figmaNode="164:13004"
      compact
      actions={
        section.is_submitted ? (
          <div className="flex flex-wrap items-center gap-2">
            {section.download_slip_href ? (
              <Link href={section.download_slip_href} className={STUDENT_BTN_OUTLINE}>
                <DownloadIcon className="size-3.5 stroke-[2]" aria-hidden />
                <span>Download slip</span>
              </Link>
            ) : null}
            <Link href={section.view_status_href} className={STUDENT_BTN_PRIMARY}>
              <span>View status</span>
              <ChevronRightIcon className="size-3.5 stroke-[2]" aria-hidden />
            </Link>
          </div>
        ) : null
      }
    >
      <RegistrationFlowStepper steps={section.steps} />

      {section.is_submitted ? (
        <>
          <div className={cn(PORTAL_CARD, "flex gap-3 border-[#bbf7d0] bg-[#f0fdf4] px-4 py-3")}>
            <CollegeAdminIcon name="info" size={18} className="mt-0.5 shrink-0 text-[#16a34a]" />
            <div>
              <p className="text-[13px] font-semibold text-[#15803d]">{section.success_title}</p>
              <p className="mt-0.5 text-[12px] text-[#166534]">{section.success_body}</p>
            </div>
          </div>

          <StAcademicsSectionCard title="Registration">
            <div className="grid gap-3 px-4 py-3 sm:grid-cols-2">
              {section.details.map((field) => (
                <StAcademicsDetailField key={field.key} label={field.label} value={field.value} />
              ))}
            </div>
          </StAcademicsSectionCard>
        </>
      ) : (
        <PendingConfirmationBanner title={section.pending_title} body={section.pending_body} />
      )}
    </StAcademicsPageBlock>
  );
}

function PendingConfirmationBanner({ title, body }: { title: string | null; body: string | null }) {
  if (!title && !body) return null;
  return (
    <div className={cn(PORTAL_CARD, "flex gap-3 border-[#e8ecf2] bg-[#f8fafc] px-4 py-3")}>
      <CollegeAdminIcon name="info" size={18} className="mt-0.5 shrink-0 text-[#6b7280]" />
      <div>
        {title ? <p className="text-[13px] font-semibold text-[#111827]">{title}</p> : null}
        {body ? <p className="mt-0.5 text-[12px] text-[#6b7280]">{body}</p> : null}
      </div>
    </div>
  );
}

function RegistrationFlowStepper({ steps }: { steps: RegistrationOverviewStep[] }) {
  return (
    <section aria-label="Registration progress" className={cn(PORTAL_CARD, "overflow-x-auto px-4 py-2.5")}>
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
  );
}