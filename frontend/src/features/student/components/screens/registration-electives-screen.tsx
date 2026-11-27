"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { XIcon } from "@/components/icons/erp/generated/x";
import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import {
  StAcademicsOutcomeBadge,
  StAcademicsPageBlock,
  StAcademicsSectionCard,
} from "@/features/student/components/ui/student-academics-figma-ui";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import { PORTAL_CARD, STUDENT_BTN_OUTLINE, STUDENT_BTN_PRIMARY } from "@/features/student/components/ui/student-portal-tokens";
import {
  useRegistrationElectivesPage,
  useSaveRegistrationDraft,
} from "@/features/student/hooks/use-student-registration";
import type {
  RegistrationElectiveGroupSelection,
  RegistrationElectivesPage,
  RegistrationSelectionInput,
} from "@/features/student/types/registration";
import { cn } from "@/lib/utils";

export function RegistrationElectivesScreen() {
  const { data, isLoading, isError, error, refetch } = useRegistrationElectivesPage();

  return (
    <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
      {data ? <RegistrationElectivesContent data={data} /> : null}
    </QueryState>
  );
}

function RegistrationElectivesContent({ data }: { data: RegistrationElectivesPage }) {
  const router = useRouter();
  const saveDraft = useSaveRegistrationDraft();
  const { selection, catalogue } = data;
  const [picks, setPicks] = useState<Record<string, { primary: string | null; alternate: string | null }>>({});
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    const next: Record<string, { primary: string | null; alternate: string | null }> = {};
    for (const group of selection.groups) {
      next[group.group_id] = {
        primary: group.selected_course_id,
        alternate: group.alternate_course_id,
      };
    }
    setPicks(next);
  }, [selection.groups]);

  const selectedCredits = useMemo(() => {
    let total = 0;
    for (const group of selection.groups) {
      const primary = picks[group.group_id]?.primary ?? group.selected_course_id;
      const opt = group.primary_options.find((o) => o.course_id === primary);
      if (opt) total += opt.credit_units;
    }
    return total;
  }, [picks, selection.groups]);

  const creditStatus = useMemo(() => {
    const { min_credits, max_credits } = selection.credit_check;
    const creditLabel =
      selectedCredits === Math.floor(selectedCredits)
        ? `${selectedCredits} credits`
        : `${selectedCredits} credits`;
    if (max_credits != null && selectedCredits > max_credits) {
      return { detail: creditLabel, label: "Over limit", tone: "warning" as const };
    }
    if (min_credits != null && selectedCredits < min_credits) {
      return { detail: creditLabel, label: "Below minimum", tone: "warning" as const };
    }
    return { detail: creditLabel, label: "Within limit", tone: "success" as const };
  }, [selectedCredits, selection.credit_check]);

  const buildSelections = (): RegistrationSelectionInput[] => {
    const out: RegistrationSelectionInput[] = [];
    for (const group of selection.groups) {
      const primary = picks[group.group_id]?.primary ?? group.selected_course_id;
      if (!primary) continue;
      const opt = group.primary_options.find((o) => o.course_id === primary);
      if (!opt || !opt.eligible) continue;
      out.push({
        course_id: opt.course_id,
        course_code: opt.course_code,
        registration_type: "elective",
        elective_group_id: group.group_id,
      });
    }
    return out;
  };

  const onReview = async () => {
    setSaveError(null);
    const selections = buildSelections();
    if (selections.length < selection.groups.length) {
      setSaveError("Choose one elective from each group before reviewing.");
      return;
    }
    try {
      await saveDraft.mutateAsync(selections);
      router.push(selection.review_href);
    } catch {
      setSaveError("Could not save your selection. Try again.");
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <StAcademicsPageBlock
        title={selection.page_title}
        description={selection.page_subtitle}
        figmaNode="164:11935"
        compact
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Link href={selection.cancel_href} className={STUDENT_BTN_OUTLINE}>
              <XIcon className="size-3.5 stroke-[2]" aria-hidden />
              <span>Cancel</span>
            </Link>
            <button
              type="button"
              disabled={saveDraft.isPending}
              onClick={() => void onReview()}
              className={cn(STUDENT_BTN_PRIMARY, saveDraft.isPending && "pointer-events-none opacity-70")}
            >
              <span>Review selection</span>
              <ChevronRightIcon className="size-3.5 stroke-[2]" aria-hidden />
            </button>
          </div>
        }
      >
        {saveError ? (
          <p className="text-[12px] font-medium text-[#c2410c]" role="alert">
            {saveError}
          </p>
        ) : null}

        <section aria-label="Registration progress" className={cn(PORTAL_CARD, "overflow-x-auto px-4 py-2.5")}>
          <div className="flex min-w-[640px] items-center justify-between gap-1">
            {selection.steps.map((step, idx) => {
              const isLast = idx === selection.steps.length - 1;
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

        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_200px] lg:items-start">
          <div className="grid gap-3 md:grid-cols-2">
            {selection.groups.map((group) => (
              <ElectiveGroupCard
                key={group.group_id}
                group={group}
                primary={picks[group.group_id]?.primary ?? group.selected_course_id}
                alternate={picks[group.group_id]?.alternate ?? group.alternate_course_id}
                onPrimary={(courseId) =>
                  setPicks((prev) => {
                    const prevAlt = prev[group.group_id]?.alternate ?? group.alternate_course_id;
                    const nextAlt = prevAlt === courseId ? null : prevAlt;
                    return {
                      ...prev,
                      [group.group_id]: {
                        primary: courseId,
                        alternate: nextAlt,
                      },
                    };
                  })
                }
                onAlternate={(courseId) =>
                  setPicks((prev) => ({
                    ...prev,
                    [group.group_id]: {
                      primary: prev[group.group_id]?.primary ?? group.selected_course_id,
                      alternate: courseId || null,
                    },
                  }))
                }
              />
            ))}
          </div>

          <StAcademicsSectionCard title="Credit check">
            <ul className="divide-y divide-[#e8ecf2]">
              <li className="flex items-start justify-between gap-2 px-4 py-2.5">
                <div className="flex gap-2">
                  <CollegeAdminIcon name="check" size={16} className="mt-0.5 shrink-0 text-[#6b7280]" />
                  <div>
                    <p className="text-[13px] font-medium text-[#111827]">Selected</p>
                    <p className="mt-0.5 text-[12px] text-[#6b7280]">{creditStatus.detail}</p>
                  </div>
                </div>
                <StAcademicsOutcomeBadge label={creditStatus.label} tone={creditStatus.tone} />
              </li>
              <li className="flex items-start gap-2 px-4 py-2.5">
                <CollegeAdminIcon name="info" size={16} className="mt-0.5 shrink-0 text-[#6b7280]" />
                <div>
                  <p className="text-[13px] font-medium text-[#111827]">Allowed</p>
                  <p className="mt-0.5 text-[12px] text-[#6b7280]">{selection.credit_check.allowed_range}</p>
                </div>
              </li>
            </ul>
          </StAcademicsSectionCard>
        </div>
      </StAcademicsPageBlock>

      <section className="scroll-mt-4 border-t border-[#e8ecf2] pt-3">
        <StAcademicsPageBlock
          title={catalogue.page_title}
          description={catalogue.page_subtitle}
          figmaNode="165:64361"
          compact
        >
          <div className="grid gap-3 md:grid-cols-2">
            {catalogue.groups.map((group) => (
              <StAcademicsSectionCard key={group.title} title={group.title} footer={<span>{group.footer_label}</span>}>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-[13px]">
                    <thead>
                      <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
                        <th className="px-4 py-2 font-medium">Code</th>
                        <th className="px-4 py-2 font-medium">Course</th>
                        <th className="px-4 py-2 text-right font-medium">Seats</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#e8ecf2]">
                      {group.courses.map((row) => (
                        <tr key={row.course_code}>
                          <td className="px-4 py-2 font-semibold text-[#172b45]">{row.course_code}</td>
                          <td className="px-4 py-2 text-[#6b7280]">{row.course_name}</td>
                          <td
                            className={cn(
                              "px-4 py-2 text-right text-[#6b7280]",
                              row.seats_label === "Full" && "font-medium text-[#c2410c]",
                            )}
                          >
                            {row.seats_label}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </StAcademicsSectionCard>
            ))}
          </div>
        </StAcademicsPageBlock>
      </section>
    </div>
  );
}

function ElectiveGroupCard({
  group,
  primary,
  alternate,
  onPrimary,
  onAlternate,
}: {
  group: RegistrationElectiveGroupSelection;
  primary: string | null;
  alternate: string | null;
  onPrimary: (courseId: string) => void;
  onAlternate: (courseId: string) => void;
}) {
  const alternateChoices = group.alternate_options.filter(
    (opt) => opt.course_id !== primary && opt.eligible,
  );

  return (
    <StAcademicsSectionCard title={group.title}>
      <div className="space-y-2 px-3 py-2">
        <fieldset className="min-w-0">
          <legend className="mb-1 text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
            {group.choose_label}
          </legend>
          <ul className="grid gap-1.5">
            {group.primary_options.map((opt) => {
              const selected = primary === opt.course_id;
              return (
                <li key={opt.course_id}>
                  <label
                    className={cn(
                      "flex cursor-pointer items-center gap-2 rounded-md border px-2.5 py-2 text-[13px] transition-colors",
                      selected
                        ? "border-[#245dd8] bg-[#eff6ff] text-[#111827]"
                        : "border-[#e8ecf2] text-[#111827] hover:border-[#c5d4f0] hover:bg-[#f8fafc]",
                      !opt.eligible && "cursor-not-allowed opacity-45 hover:border-[#e8ecf2] hover:bg-transparent",
                    )}
                  >
                    <input
                      type="radio"
                      name={`elective-${group.group_id}`}
                      value={opt.course_id}
                      checked={selected}
                      disabled={!opt.eligible}
                      onChange={() => onPrimary(opt.course_id)}
                      className="size-3.5 shrink-0 border-[#d1d5db] text-[#245dd8] focus:ring-[#245dd8]"
                    />
                    <span className="min-w-0 leading-snug">{opt.choice_label}</span>
                  </label>
                </li>
              );
            })}
          </ul>
        </fieldset>
        <div className="pt-0.5">
          <label htmlFor={`alternate-${group.group_id}`} className="mb-1 block text-[11px] font-medium text-[#6b7280]">
            Alternate choice
          </label>
          <select
            id={`alternate-${group.group_id}`}
            value={alternate ?? ""}
            onChange={(e) => onAlternate(e.target.value)}
            className="h-8 w-full rounded border border-[#e8ecf2] bg-white px-2.5 text-[12px] text-[#111827] focus:border-[#245dd8] focus:outline-none"
          >
            <option value="">Select alternate</option>
            {alternateChoices.map((opt) => (
              <option key={opt.course_id} value={opt.course_id}>
                {opt.choice_label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </StAcademicsSectionCard>
  );
}