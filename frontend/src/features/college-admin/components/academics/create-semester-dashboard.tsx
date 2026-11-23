"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { SaveIcon } from "@/components/icons/erp/generated/save";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { YearsSemestersSubNav } from "@/features/college-admin/components/academics/years-semesters-sub-nav";
import {
  CollegeAdminPrimaryButton,
  CollegeAdminSecondaryButton,
} from "@/features/college-admin/components/ui/college-admin-action-button";
import {
  CollegeAdminPanelChromeHeader,
  CollegeAdminPanelShell,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { CollegeAdminWizardStepper } from "@/features/college-admin/components/ui/college-admin-wizard-stepper";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useCreateSemesterManagementTerm,
  useSaveSemesterManagementSettings,
  useSemesterManagementPage,
} from "@/features/college-admin/hooks/use-semester-management";

const STEPS = [
  { key: "identity", label: "Semester identity", step_number: 1 },
  { key: "teaching", label: "Teaching period", step_number: 2 },
  { key: "milestones", label: "Exams & registration", step_number: 3 },
  { key: "review", label: "Review & create", step_number: 4 },
];

export function CreateSemesterDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const yearIdParam = useMemo(() => searchParams.get("academic_year_id") ?? undefined, [searchParams]);

  const { data, isLoading, isError, error, refetch } = useSemesterManagementPage({
    academic_year_id: yearIdParam,
  });
  const createTerm = useCreateSemesterManagementTerm();
  const saveSettings = useSaveSemesterManagementSettings();

  const [activeStep, setActiveStep] = useState("identity");
  const [label, setLabel] = useState("");
  const [yearId, setYearId] = useState(yearIdParam ?? "");
  const [teachingStarts, setTeachingStarts] = useState("");
  const [lastInstruction, setLastInstruction] = useState("");
  const [midExam, setMidExam] = useState("");
  const [endExam, setEndExam] = useState("");
  const [regOpens, setRegOpens] = useState("");
  const [addDrop, setAddDrop] = useState("");

  const stepIndex = STEPS.findIndex((s) => s.key === activeStep);
  const wizardSteps = STEPS.map((step, index) => ({
    ...step,
    status: index < stepIndex ? "done" : step.key === activeStep ? "active" : "pending",
  }));

  const subNav = [
    { key: "years", label: "Years", href: "/college-admin/academics/academic-year-management", active: false },
    { key: "semesters", label: "Semesters", href: "/college-admin/academics/semester-management", active: true },
    {
      key: "calendar",
      label: "Academic calendar",
      href: "/college-admin/academics/academic-calendar-configuration",
      active: false,
    },
  ];

  const yearOptions = data?.year_filter_options.filter((o) => o.value) ?? [];

  useEffect(() => {
    if (yearIdParam) {
      setYearId(yearIdParam);
      return;
    }
    if (!yearId && data?.selected_academic_year_id) {
      setYearId(data.selected_academic_year_id);
    }
  }, [yearIdParam, data?.selected_academic_year_id, yearId]);

  function continueStep() {
    if (activeStep === "identity") {
      if (!yearId || label.trim().length < 2) {
        toast.error("Choose an academic year and enter a semester name.");
        return;
      }
      setActiveStep("teaching");
      return;
    }
    if (activeStep === "teaching") {
      if (!teachingStarts || !lastInstruction) {
        toast.error("Teaching start and last instruction day are required.");
        return;
      }
      setActiveStep("milestones");
      return;
    }
    if (activeStep === "milestones") {
      if (!endExam) {
        toast.error("End-semester exam date is required.");
        return;
      }
      setActiveStep("review");
    }
  }

  function finalize() {
    if (!yearId || !label.trim()) return;
    createTerm.mutate(
      { academic_year_id: yearId, label: label.trim() },
      {
        onSuccess: async (page) => {
          const termId = page.selected_term_id;
          if (!termId) {
            toast.error("Semester was created but settings could not be saved.");
            return;
          }
          saveSettings.mutate(
            {
              term_id: termId,
              settings: {
                teaching_starts: teachingStarts || null,
                last_instruction_day: lastInstruction || null,
                mid_semester_exam_date: midExam || null,
                end_semester_exam_date: endExam || null,
                course_registration_opens: regOpens || null,
                add_drop_deadline: addDrop || null,
              },
            },
            {
              onSuccess: () => {
                toast.success("Semester created");
                const q = new URLSearchParams({ term_id: termId });
                if (yearId) q.set("academic_year_id", yearId);
                router.replace(`/college-admin/academics/semester-details?${q.toString()}`);
              },
            },
          );
        },
      },
    );
  }

  const busy = createTerm.isPending || saveSettings.isPending;

  return (
    <div className="space-y-5">
      <YearsSemestersSubNav items={subNav} />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-1">
            <Link
              href="/college-admin/academics/semester-management"
              className="inline-flex size-8 shrink-0 items-center justify-center rounded-md text-[#374151] hover:bg-[#f3f4f6]"
              aria-label="Back"
            >
              <ChevronLeftIcon className="size-5" />
            </Link>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">New semester</h2>
          </div>
          <p className="mt-1 pl-9 text-[14px] text-[#6b7280]">
            Step {stepIndex + 1} of {STEPS.length} · {STEPS[stepIndex]?.label}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <CollegeAdminSecondaryButton disabled={busy}>
            <SaveIcon className="size-3.5" aria-hidden />
            Save draft
          </CollegeAdminSecondaryButton>
          {activeStep === "review" ? (
            <CollegeAdminPrimaryButton disabled={busy} onClick={finalize}>
              Create semester
            </CollegeAdminPrimaryButton>
          ) : (
            <CollegeAdminPrimaryButton disabled={busy} onClick={continueStep}>
              Continue
              <ChevronRightIcon className="size-3.5" aria-hidden />
            </CollegeAdminPrimaryButton>
          )}
        </div>
      </div>

      <CollegeAdminWizardStepper steps={wizardSteps} activeKey={activeStep} />

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <CollegeAdminPanelShell>
            <CollegeAdminPanelChromeHeader title={STEPS[stepIndex]?.label ?? "Semester setup"} />
            <div className="px-5 py-4">
            {activeStep === "identity" ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label className="text-[13px] text-[#374151]">
                    Academic year <span className="text-[#dc2626]">*</span>
                  </Label>
                  <select
                    className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                    value={yearId}
                    onChange={(e) => setYearId(e.target.value)}
                  >
                    {yearOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label className="text-[13px] text-[#374151]">
                    Semester name <span className="text-[#dc2626]">*</span>
                  </Label>
                  <Input
                    className="mt-1.5 h-9"
                    placeholder="e.g. Odd semester"
                    value={label}
                    onChange={(e) => setLabel(e.target.value)}
                  />
                </div>
              </div>
            ) : null}

            {activeStep === "teaching" ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <DateField label="Teaching starts *" value={teachingStarts} onChange={setTeachingStarts} />
                <DateField label="Last instruction day *" value={lastInstruction} onChange={setLastInstruction} />
              </div>
            ) : null}

            {activeStep === "milestones" ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <DateField label="Mid-semester exams" value={midExam} onChange={setMidExam} />
                <DateField label="End-semester exams *" value={endExam} onChange={setEndExam} />
                <DateField label="Course registration opens" value={regOpens} onChange={setRegOpens} />
                <DateField label="Add / drop deadline" value={addDrop} onChange={setAddDrop} />
              </div>
            ) : null}

            {activeStep === "review" ? (
              <dl className="divide-y divide-[#f1f5f9] text-[13px]">
                <SummaryRow label="Semester" value={label} />
                <SummaryRow
                  label="Academic year"
                  value={yearOptions.find((o) => o.value === yearId)?.label ?? "—"}
                />
                <SummaryRow label="Teaching" value={`${teachingStarts || "—"} → ${lastInstruction || "—"}`} />
                <SummaryRow label="End-semester exam" value={endExam || "—"} />
              </dl>
            ) : null}
            </div>
          </CollegeAdminPanelShell>
        ) : null}
      </QueryState>
    </div>
  );
}

function DateField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <Label className="text-[13px] text-[#374151]">{label}</Label>
      <Input className="mt-1.5 h-9" type="date" value={value} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 py-3 first:pt-0">
      <dt className="text-[#6b7280]">{label}</dt>
      <dd className="font-medium text-[#111827]">{value}</dd>
    </div>
  );
}
