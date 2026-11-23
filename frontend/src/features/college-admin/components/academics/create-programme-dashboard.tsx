"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CollegeAdminPrimaryButton } from "@/features/college-admin/components/ui/college-admin-action-button";
import {
  CollegeAdminPanelChromeHeader,
  CollegeAdminPanelShell,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { CollegeAdminWizardStepper } from "@/features/college-admin/components/ui/college-admin-wizard-stepper";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useCreateProgrammeManagement,
  useProgrammeManagementPage,
} from "@/features/college-admin/hooks/use-programme-management";

const STEPS = [
  { key: "identity", label: "Identity", step_number: 1 },
  { key: "affiliation", label: "Department & regulation", step_number: 2 },
  { key: "structure", label: "Duration & intake", step_number: 3 },
  { key: "admission", label: "Admissions", step_number: 4 },
  { key: "review", label: "Review & create", step_number: 5 },
];

function SelectField({
  label,
  value,
  onChange,
  options,
  required,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  required?: boolean;
}) {
  return (
    <div>
      <Label className="text-[13px] font-medium text-[#374151]">
        {label}
        {required ? <span className="text-[#dc2626]"> *</span> : null}
      </Label>
      <select
        className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#111827]"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((opt) => (
          <option key={`${opt.value}-${opt.label}`} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

export function CreateProgrammeDashboard() {
  const router = useRouter();
  const { data, isLoading, isError, error, refetch } = useProgrammeManagementPage({ page: 1 });
  const createProgramme = useCreateProgrammeManagement();

  const [activeStep, setActiveStep] = useState("identity");
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [shortName, setShortName] = useState("");
  const [description, setDescription] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [level, setLevel] = useState("");
  const [regulation, setRegulation] = useState("");
  const [duration, setDuration] = useState("8");
  const [credits, setCredits] = useState("160");
  const [intake, setIntake] = useState("");
  const [mode, setMode] = useState("full_time");
  const [entryQualification, setEntryQualification] = useState("");

  const stepIndex = STEPS.findIndex((s) => s.key === activeStep);
  const wizardSteps = STEPS.map((step, index) => ({
    ...step,
    status: index < stepIndex ? "done" : step.key === activeStep ? "active" : "pending",
  }));

  function continueStep() {
    if (activeStep === "identity") {
      if (!name.trim() || !code.trim()) {
        toast.error("Programme name and code are required.");
        return;
      }
      setActiveStep("affiliation");
      return;
    }
    if (activeStep === "affiliation") {
      if (!departmentId) {
        toast.error("Select the owning department.");
        return;
      }
      setActiveStep("structure");
      return;
    }
    if (activeStep === "structure") {
      const sem = Number(duration);
      const cred = Number(credits);
      if (!Number.isFinite(sem) || sem < 1) {
        toast.error("Enter a valid duration in semesters.");
        return;
      }
      if (!Number.isFinite(cred) || cred < 0) {
        toast.error("Enter valid credits required.");
        return;
      }
      setActiveStep("admission");
      return;
    }
    if (activeStep === "admission") {
      setActiveStep("review");
    }
  }

  function finalize() {
    const sem = Number(duration);
    const cred = Number(credits);
    const intakeNum = intake.trim() ? Number(intake) : null;
    if (intake.trim() && (!Number.isFinite(intakeNum) || intakeNum! < 0)) {
      toast.error("Approved intake must be a positive number.");
      return;
    }
    createProgramme.mutate(
      {
        name: name.trim(),
        programme_code: code.trim(),
        short_name: shortName.trim() || null,
        description: description.trim() || null,
        department_id: departmentId || null,
        programme_level: level || null,
        regulation_code: regulation || null,
        mode_of_study: mode,
        approved_intake: intakeNum,
        entry_qualification: entryQualification.trim() || null,
        duration_semesters: sem,
        credits_required: cred,
      },
      {
        onSuccess: (result) => {
          router.replace(result.detail_href);
        },
      },
    );
  }

  const deptOptions = data?.create_department_options ?? [];
  const levelOptions = data?.create_level_options ?? [];
  const regOptions = data?.create_regulation_options ?? [];
  const modeOptions = data?.create_mode_options ?? [];

  const busy = createProgramme.isPending;

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-1">
            <Link
              href="/college-admin/academics/programme-management"
              className="inline-flex size-8 shrink-0 items-center justify-center rounded-md text-[#374151] hover:bg-[#f3f4f6]"
              aria-label="Back"
            >
              <ChevronLeftIcon className="size-5" />
            </Link>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">New programme</h2>
          </div>
          <p className="mt-1 pl-9 text-[14px] text-[#6b7280]">
            Step {stepIndex + 1} of {STEPS.length} · {STEPS[stepIndex]?.label}
          </p>
          <p className="mt-1 pl-9 text-[13px] text-[#64748b]">
            {data?.create_form_note ?? "New programmes are saved as proposed until published through academic configuration."}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          {activeStep === "review" ? (
            <CollegeAdminPrimaryButton disabled={busy} onClick={finalize}>
              {data?.create_submit_label ?? "Create programme"}
            </CollegeAdminPrimaryButton>
          ) : (
            <CollegeAdminPrimaryButton disabled={busy} onClick={continueStep}>
              Continue
              <ChevronRightIcon className="size-3.5" aria-hidden />
            </CollegeAdminPrimaryButton>
          )}
          <Link
            href="/college-admin/academics/programme-management"
            className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-semibold text-[#374151] hover:bg-[#f9fafb]"
          >
            Cancel
          </Link>
        </div>
      </div>

      <CollegeAdminWizardStepper steps={wizardSteps} activeKey={activeStep} />

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <CollegeAdminPanelShell>
            <CollegeAdminPanelChromeHeader title={STEPS[stepIndex]?.label ?? "Programme setup"} />
            <div className="space-y-4 px-5 py-4">
              {activeStep === "identity" ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="sm:col-span-2">
                    <Label className="text-[13px] font-medium text-[#374151]">
                      Programme name <span className="text-[#dc2626]">*</span>
                    </Label>
                    <Input className="mt-1.5 h-9" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. B.E. Computer Science and Engineering" />
                  </div>
                  <div>
                    <Label className="text-[13px] font-medium text-[#374151]">
                      Programme code <span className="text-[#dc2626]">*</span>
                    </Label>
                    <Input className="mt-1.5 h-9 font-mono text-[13px]" value={code} onChange={(e) => setCode(e.target.value)} placeholder="BE-CSE" />
                  </div>
                  <div>
                    <Label className="text-[13px] font-medium text-[#374151]">Short name</Label>
                    <Input className="mt-1.5 h-9" value={shortName} onChange={(e) => setShortName(e.target.value)} placeholder="B.E. CSE" />
                  </div>
                  <div className="sm:col-span-2">
                    <Label className="text-[13px] font-medium text-[#374151]">Description</Label>
                    <textarea
                      className="mt-1.5 min-h-[88px] w-full resize-y rounded-md border border-[#dce3ec] bg-white px-3 py-2 text-[13px] text-[#111827] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-[#245dd8]"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Outline outcomes, accreditation, or notes for administrators."
                    />
                  </div>
                </div>
              ) : null}

              {activeStep === "affiliation" ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  <SelectField
                    label="Owning department"
                    required
                    value={departmentId}
                    onChange={setDepartmentId}
                    options={deptOptions}
                  />
                  <SelectField label="Programme level" value={level} onChange={setLevel} options={levelOptions} />
                  <div className="sm:col-span-2">
                    <SelectField label="Regulation version" value={regulation} onChange={setRegulation} options={regOptions} />
                  </div>
                </div>
              ) : null}

              {activeStep === "structure" ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <Label className="text-[13px] font-medium text-[#374151]">
                      Duration (semesters) <span className="text-[#dc2626]">*</span>
                    </Label>
                    <Input className="mt-1.5 h-9" type="number" min={1} max={20} value={duration} onChange={(e) => setDuration(e.target.value)} />
                  </div>
                  <div>
                    <Label className="text-[13px] font-medium text-[#374151]">
                      Credits required <span className="text-[#dc2626]">*</span>
                    </Label>
                    <Input className="mt-1.5 h-9" type="number" min={0} value={credits} onChange={(e) => setCredits(e.target.value)} />
                  </div>
                  <div>
                    <Label className="text-[13px] font-medium text-[#374151]">Approved intake (per year)</Label>
                    <Input className="mt-1.5 h-9" type="number" min={0} value={intake} onChange={(e) => setIntake(e.target.value)} placeholder="e.g. 60" />
                  </div>
                  <SelectField label="Mode of study" value={mode} onChange={setMode} options={modeOptions} />
                </div>
              ) : null}

              {activeStep === "admission" ? (
                <div>
                  <Label className="text-[13px] font-medium text-[#374151]">Entry qualification</Label>
                  <textarea
                    className="mt-1.5 min-h-[120px] w-full resize-y rounded-md border border-[#dce3ec] bg-white px-3 py-2 text-[13px] text-[#111827] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-[#245dd8]"
                    value={entryQualification}
                    onChange={(e) => setEntryQualification(e.target.value)}
                    placeholder="e.g. Pass in HSC with Physics, Chemistry and Mathematics — or equivalent as per university norms."
                  />
                </div>
              ) : null}

              {activeStep === "review" ? (
                <dl className="divide-y divide-[#f1f5f9] text-[13px]">
                  <Row label="Programme" value={name} />
                  <Row label="Code" value={code.toUpperCase()} />
                  <Row label="Department" value={deptOptions.find((o) => o.value === departmentId)?.label ?? "—"} />
                  <Row label="Level" value={levelOptions.find((o) => o.value === level)?.label ?? "Inferred from duration"} />
                  <Row label="Regulation" value={regOptions.find((o) => o.value === regulation)?.label ?? "—"} />
                  <Row label="Structure" value={`${duration} semesters · ${credits} credits · ${modeOptions.find((o) => o.value === mode)?.label ?? mode}`} />
                  <Row label="Intake" value={intake.trim() ? intake : "—"} />
                  <Row label="Entry qualification" value={entryQualification.trim() || "—"} />
                </dl>
              ) : null}
            </div>
          </CollegeAdminPanelShell>
        ) : null}
      </QueryState>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 py-3 first:pt-0">
      <dt className="text-[#64748b]">{label}</dt>
      <dd className="max-w-[60%] text-right font-medium text-[#111827]">{value}</dd>
    </div>
  );
}