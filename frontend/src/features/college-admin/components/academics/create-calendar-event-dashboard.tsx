"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
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
  useAcademicCalendarConfigurationPage,
  useAddAcademicCalendarEvent,
} from "@/features/college-admin/hooks/use-academic-calendar-configuration";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const STEPS = [
  { key: "event", label: "Event details", step_number: 1 },
  { key: "schedule", label: "Schedule", step_number: 2 },
  { key: "audience", label: "Audience", step_number: 3 },
  { key: "review", label: "Review & save", step_number: 4 },
];

export function CreateCalendarEventDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const yearIdParam = useMemo(() => searchParams.get("academic_year_id") ?? undefined, [searchParams]);

  const { data, isLoading, isError, error, refetch } = useAcademicCalendarConfigurationPage({
    academic_year_id: yearIdParam,
  });
  const addEvent = useAddAcademicCalendarEvent();

  const [activeStep, setActiveStep] = useState("event");
  const [title, setTitle] = useState("");
  const [eventType, setEventType] = useState("academic");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [audience, setAudience] = useState("all");

  const formMeta = data?.add_event_form;

  useEffect(() => {
    if (!formMeta) return;
    setEventType(formMeta.type_default_value);
    setAudience(formMeta.audience_default_value);
  }, [formMeta]);

  const stepIndex = STEPS.findIndex((s) => s.key === activeStep);
  const wizardSteps = STEPS.map((step, index) => ({
    ...step,
    status: index < stepIndex ? "done" : step.key === activeStep ? "active" : "pending",
  }));

  const subNav = data?.sub_nav ?? [];

  function continueStep() {
    if (activeStep === "event") {
      if (!title.trim()) {
        toast.error("Enter an event title.");
        return;
      }
      setActiveStep("schedule");
      return;
    }
    if (activeStep === "schedule") {
      if (!fromDate) {
        toast.error("Choose a start date.");
        return;
      }
      if (toDate && toDate < fromDate) {
        toast.error("End date must be on or after the start date.");
        return;
      }
      setActiveStep("audience");
      return;
    }
    if (activeStep === "audience") {
      setActiveStep("review");
    }
  }

  function finalize() {
    if (!data?.selected_academic_year_id) return;
    addEvent.mutate(
      {
        academic_year_id: data.selected_academic_year_id,
        title: title.trim(),
        event_type: eventType,
        from_date: fromDate,
        to_date: toDate.trim() || null,
        audience,
      },
      {
        onSuccess: () => {
          toast.success("Event saved");
          router.replace("/college-admin/academics/academic-calendar-configuration");
        },
      },
    );
  }

  return (
    <div className="space-y-5">
      {subNav.length ? <YearsSemestersSubNav items={subNav} /> : null}

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-1">
            <Link
              href="/college-admin/academics/academic-calendar-configuration"
              className="inline-flex size-8 shrink-0 items-center justify-center rounded-md text-[#374151] hover:bg-[#f3f4f6]"
              aria-label="Back"
            >
              <ChevronLeftIcon className="size-5" />
            </Link>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">Add calendar event</h2>
          </div>
          <p className="mt-1 pl-9 text-[14px] text-[#6b7280]">
            Step {stepIndex + 1} of {STEPS.length} · {STEPS[stepIndex]?.label}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          {activeStep === "review" ? (
            <CollegeAdminPrimaryButton disabled={addEvent.isPending} onClick={finalize}>
              Save event
            </CollegeAdminPrimaryButton>
          ) : (
            <CollegeAdminPrimaryButton disabled={addEvent.isPending} onClick={continueStep}>
              Continue
              <ChevronRightIcon className="size-3.5" aria-hidden />
            </CollegeAdminPrimaryButton>
          )}
        </div>
      </div>

      <CollegeAdminWizardStepper steps={wizardSteps} activeKey={activeStep} />

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data && formMeta ? (
          <CollegeAdminPanelShell>
            <CollegeAdminPanelChromeHeader title={STEPS[stepIndex]?.label ?? "Calendar event"} />
            <div className="px-5 py-4">
            {activeStep === "event" ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <Label className="text-[13px] text-[#374151]">
                    {formMeta.title_meta.label} <span className="text-[#dc2626]">*</span>
                  </Label>
                  <Input
                    className="mt-1.5 h-9"
                    placeholder={formMeta.title_placeholder}
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                  />
                </div>
                <div>
                  <Label className="text-[13px] text-[#374151]">{formMeta.type_meta.label} *</Label>
                  <select
                    className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                    value={eventType}
                    onChange={(e) => setEventType(e.target.value)}
                  >
                    {formMeta.type_options.map((opt) => (
                      <option key={opt.value || opt.label} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            ) : null}

            {activeStep === "schedule" ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label className="text-[13px] text-[#374151]">{formMeta.from_meta.label} *</Label>
                  <Input className="mt-1.5 h-9" type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
                </div>
                <div>
                  <Label className="text-[13px] text-[#374151]">{formMeta.to_meta.label}</Label>
                  <Input className="mt-1.5 h-9" type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
                </div>
              </div>
            ) : null}

            {activeStep === "audience" ? (
              <div className="max-w-sm">
                <Label className="text-[13px] text-[#374151]">{formMeta.audience_meta.label} *</Label>
                <select
                  className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                  value={audience}
                  onChange={(e) => setAudience(e.target.value)}
                >
                  {formMeta.audience_options.map((opt) => (
                    <option key={opt.value || opt.label} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            ) : null}

            {activeStep === "review" ? (
              <dl className="divide-y divide-[#f1f5f9] text-[13px]">
                <Row label="Title" value={title} />
                <Row label="Type" value={eventType} />
                <Row label="Dates" value={`${fromDate} → ${toDate || fromDate}`} />
                <Row label="Audience" value={audience} />
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
      <dt className="text-[#6b7280]">{label}</dt>
      <dd className="font-medium text-[#111827]">{value}</dd>
    </div>
  );
}