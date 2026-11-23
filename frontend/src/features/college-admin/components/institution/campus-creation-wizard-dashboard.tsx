"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef } from "react";
import { useForm } from "react-hook-form";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { SaveIcon } from "@/components/icons/erp/generated/save";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useCampusCreationPage,
  useFinishCampusCreation,
  usePatchCampusCreationStep,
  useSaveCampusCreationDraft,
} from "@/features/college-admin/hooks/use-campus-creation";
import { CAMPUS_CREATION_FIELD_META_BY_STEP } from "@/features/college-admin/components/institution/campus-creation-field-meta";
import type { CampusCreationFormValues, CampusCreationWizardStep } from "@/features/college-admin/types/campus-creation";
import type { InstitutionFieldMeta } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

const STEP_ORDER = ["identity", "location", "contact", "capacity", "facilities", "review"] as const;

function metaFor(fieldMeta: InstitutionFieldMeta[], key: string) {
  return fieldMeta.find((row) => row.key === key);
}

function FormField({ meta, children }: { meta?: InstitutionFieldMeta; children: React.ReactNode }) {
  if (!meta) return null;
  return (
    <div
      className={cn("space-y-1.5", meta.field_type === "textarea" ? "sm:col-span-2" : undefined)}
      data-field-key={meta.key}
    >
      <Label className="text-[13px] font-medium text-[#374151]">
        {meta.label}
        {meta.required ? <span className="text-[#dc2626]"> *</span> : null}
      </Label>
      {children}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="border-b border-[#f1f5f9] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
      </div>
      <div className="px-5 py-4">{children}</div>
    </section>
  );
}

function CampusWizardStepper({
  steps,
  activeKey,
  onStep,
}: {
  steps: CampusCreationWizardStep[];
  activeKey: string;
  onStep: (key: string) => void;
}) {
  const activeIndex = steps.findIndex((s) => s.key === activeKey);
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white px-4 py-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:px-8">
      <div className="flex items-start">
        {steps.map((wizardStep, index) => {
          const active = wizardStep.key === activeKey;
          const done = index < activeIndex || wizardStep.status === "done";
          return (
            <div key={wizardStep.key} className="flex min-w-0 flex-1 items-center last:flex-none">
              <button
                type="button"
                onClick={() => onStep(wizardStep.key)}
                className="flex min-w-0 flex-col items-center gap-1 text-center sm:items-start sm:text-left"
              >
                <span className="flex items-center gap-2">
                  <span
                    className={cn(
                      "flex size-8 shrink-0 items-center justify-center rounded-full text-[13px] font-semibold tabular-nums",
                      active && "border-2 border-[#245dd8] bg-white text-[#245dd8]",
                      !active && !done && "border border-[#e5e7eb] bg-[#f9fafb] text-[#9ca3af]",
                      done && !active && "border-2 border-[#245dd8] bg-[#245dd8] text-white",
                    )}
                    aria-current={active ? "step" : undefined}
                  >
                    {done && !active ? (
                      <CheckIcon className="size-3.5" strokeWidth={2.5} aria-hidden />
                    ) : (
                      wizardStep.step_number
                    )}
                  </span>
                  <span className="hidden min-w-0 sm:block">
                    <span
                      className={cn(
                        "block truncate text-[13px]",
                        active || done ? "font-semibold text-[#245dd8]" : "font-medium text-[#9ca3af]",
                      )}
                    >
                      {wizardStep.label}
                    </span>
                    {wizardStep.subtitle ? (
                      <span className="block truncate text-[11px] text-[#9ca3af]">{wizardStep.subtitle}</span>
                    ) : null}
                  </span>
                </span>
              </button>
              {index < steps.length - 1 ? (
                <div
                  className={cn(
                    "mx-3 hidden h-px min-w-[1.5rem] flex-1 sm:block",
                    index < activeIndex ? "bg-[#245dd8]" : "bg-[#e5e7eb]",
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

const STEP_TITLES: Record<string, string> = {
  identity: "Campus identity",
  location: "Location & address",
  contact: "Contact & regional settings",
  capacity: "Area & capacity",
  facilities: "Facilities planning",
  review: "Review & confirm",
};

const selectClassName =
  "h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#111827]";
const inputClassName = "h-9 border-[#dce3ec] text-[13px]";

function ReviewRow({ label, value }: { label: string; value: string | null | undefined }) {
  const text = (value ?? "").trim();
  if (!text) return null;
  return (
    <div className="flex justify-between gap-4 border-b border-[#f1f5f9] py-2 text-[13px] last:border-0">
      <span className="text-[#6b7280]">{label}</span>
      <span className="max-w-[60%] text-right font-medium text-[#111827]">{text}</span>
    </div>
  );
}

export function CampusCreationWizardDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const campusIdParam = useMemo(() => searchParams.get("campus_id") ?? undefined, [searchParams]);

  const pageQuery = useCampusCreationPage(campusIdParam);
  const saveDraft = useSaveCampusCreationDraft(campusIdParam);
  const patchStep = usePatchCampusCreationStep(campusIdParam);
  const finish = useFinishCampusCreation();

  const data = pageQuery.data;
  const form = useForm<CampusCreationFormValues>({ values: data?.form });
  const savingRef = useRef(false);

  const activeStep = (() => {
    const key = data?.current_step_key ?? "identity";
    return STEP_ORDER.includes(key as (typeof STEP_ORDER)[number])
      ? (key as (typeof STEP_ORDER)[number])
      : "identity";
  })();

  const fieldMeta = CAMPUS_CREATION_FIELD_META_BY_STEP[activeStep] ?? [];
  const toPayload = (values: CampusCreationFormValues) => ({ ...values });

  const persistStepUrl = (stepKey: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("step", stepKey);
    if (campusIdParam) params.set("campus_id", campusIdParam);
    router.push(`/college-admin/institution/campuses/new?${params.toString()}`);
  };

  const silentSave = useCallback(
    (values: CampusCreationFormValues, stepKey: string, advance = false) => {
      if (!data || savingRef.current) return;
      savingRef.current = true;
      saveDraft.mutate(
        {
          draft_id: data.draft_id,
          step_key: stepKey,
          values: toPayload(values),
          advance,
        },
        {
          onSettled: () => {
            savingRef.current = false;
          },
        },
      );
    },
    [data, saveDraft],
  );

  useEffect(() => {
    const onVisibility = () => {
      if (document.visibilityState === "hidden" && data) {
        silentSave(form.getValues(), activeStep);
      }
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, [activeStep, data, form, silentSave]);

  const handleSaveDraft = form.handleSubmit((values) => {
    if (!data) return;
    saveDraft.mutate(
      { draft_id: data.draft_id, step_key: activeStep, values: toPayload(values) },
      {
        onSuccess: () => toast.success("Draft saved — you can continue later"),
        onError: onCollegeAdminMutationError,
      },
    );
  });

  const handleContinue = form.handleSubmit((values) => {
    if (!data) return;
    saveDraft.mutate(
      { draft_id: data.draft_id, step_key: activeStep, values: toPayload(values), advance: true },
      {
        onSuccess: (res) => {
          persistStepUrl(res.current_step_key);
          toast.success("Step saved");
        },
        onError: onCollegeAdminMutationError,
      },
    );
  });

  const handleBackStep = () => {
    const idx = STEP_ORDER.indexOf(activeStep);
    if (idx <= 0 || !data) return;
    const prev = STEP_ORDER[idx - 1];
    const fromStep = activeStep;
    patchStep(prev);
    persistStepUrl(prev);
    saveDraft.mutate(
      {
        draft_id: data.draft_id,
        step_key: fromStep,
        values: toPayload(form.getValues()),
        retreat: true,
      },
      {
        onSuccess: (res) => {
          patchStep(res.current_step_key);
          persistStepUrl(res.current_step_key);
        },
        onError: (e: Error) => {
          patchStep(fromStep);
          void pageQuery.refetch();
          toast.error(e.message || "Could not go back — try again");
        },
      },
    );
  };

  const handleFinish = form.handleSubmit((values) => {
    if (!data) return;
    saveDraft.mutate(
      { draft_id: data.draft_id, step_key: "review", values: toPayload(values) },
      {
        onSuccess: () => {
          finish.mutate(
            { draft_id: data.draft_id, values: toPayload(values) },
            {
              onSuccess: (res) => {
                toast.success(res.message);
                router.push(res.detail_href);
              },
              onError: onCollegeAdminMutationError,
            },
          );
        },
        onError: onCollegeAdminMutationError,
      },
    );
  });

  const handleStepJump = (key: string) => {
    if (!data) return;
    saveDraft.mutate(
      { draft_id: data.draft_id, step_key: key, values: toPayload(form.getValues()) },
      { onSuccess: (res) => persistStepUrl(res.current_step_key) },
    );
  };

  const isBusy = saveDraft.isPending || finish.isPending;
  const isLast = activeStep === "review";
  const v = form.watch();

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-1">
            <Link
              href={data?.back_href ?? "/college-admin/institution/campuses"}
              className="inline-flex size-8 shrink-0 items-center justify-center rounded-md text-[#374151] hover:bg-[#f3f4f6]"
              aria-label={data?.back_label ?? "Back"}
            >
              <ChevronLeftIcon className="size-5" />
            </Link>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
              {data?.page_title ?? "Create campus"}
            </h2>
          </div>
          <p className="mt-1 pl-9 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Step-by-step campus registration with draft save"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            disabled={!data || isBusy}
            onClick={() => void handleSaveDraft()}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
          >
            <SaveIcon className="size-3.5" aria-hidden />
            {data?.save_draft_label ?? "Save draft"}
          </button>
        </div>
      </div>

      {data ? <CampusWizardStepper steps={data.steps} activeKey={activeStep} onStep={handleStepJump} /> : null}

      <QueryState
        isLoading={pageQuery.isLoading}
        isError={pageQuery.isError}
        error={pageQuery.error}
        onRetry={() => void pageQuery.refetch()}
      >
        {data ? (
          <Section title={STEP_TITLES[activeStep] ?? "Details"}>
            {activeStep === "identity" ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField meta={metaFor(fieldMeta, "campus_code")}>
                  <Input
                    className={inputClassName}
                    {...form.register("campus_code")}
                    placeholder="e.g. MAIN"
                    disabled={data.is_edit_mode}
                    autoComplete="off"
                  />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "name")}>
                  <Input className={inputClassName} {...form.register("name")} placeholder="Official campus name" />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "is_main")}>
                  <label className="flex h-9 cursor-pointer items-center gap-2 text-[13px] text-[#374151]">
                    <input
                      type="checkbox"
                      className="size-4 rounded border-[#dce3ec]"
                      checked={v.is_main === "true"}
                      onChange={(e) => form.setValue("is_main", e.target.checked ? "true" : "false")}
                    />
                    Set as main campus
                  </label>
                </FormField>
              </div>
            ) : null}

            {activeStep === "location" ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField meta={metaFor(fieldMeta, "address_line1")}>
                  <Input className={inputClassName} {...form.register("address_line1")} />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "address_line2")}>
                  <Input className={inputClassName} {...form.register("address_line2")} />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "city")}>
                  <Input className={inputClassName} {...form.register("city")} />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "district")}>
                  <Input className={inputClassName} {...form.register("district")} />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "state")}>
                  <Input className={inputClassName} {...form.register("state")} />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "country")}>
                  <Input className={inputClassName} {...form.register("country")} />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "postal_code")}>
                  <Input className={inputClassName} {...form.register("postal_code")} />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "latitude")}>
                  <Input className={inputClassName} {...form.register("latitude")} />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "longitude")}>
                  <Input className={inputClassName} {...form.register("longitude")} />
                </FormField>
              </div>
            ) : null}

            {activeStep === "contact" ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField meta={metaFor(fieldMeta, "contact_email")}>
                  <Input className={inputClassName} type="email" {...form.register("contact_email")} />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "contact_phone")}>
                  <Input className={inputClassName} {...form.register("contact_phone")} />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "timezone")}>
                  <select className={selectClassName} {...form.register("timezone")}>
                    {data.timezone_options.map((opt) => (
                      <option key={opt.value || opt.label} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </FormField>
                <FormField meta={metaFor(fieldMeta, "locale")}>
                  <select className={selectClassName} {...form.register("locale")}>
                    {data.locale_options.map((opt) => (
                      <option key={opt.value || opt.label} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </FormField>
              </div>
            ) : null}

            {activeStep === "capacity" ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField meta={metaFor(fieldMeta, "area_acres")}>
                  <Input className={inputClassName} inputMode="decimal" {...form.register("area_acres")} />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "built_up_sq_m")}>
                  <Input className={inputClassName} inputMode="decimal" {...form.register("built_up_sq_m")} />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "buildings_count")}>
                  <Input className={inputClassName} inputMode="numeric" {...form.register("buildings_count")} />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "parking_slots")}>
                  <Input className={inputClassName} inputMode="numeric" {...form.register("parking_slots")} />
                </FormField>
              </div>
            ) : null}

            {activeStep === "facilities" ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField meta={metaFor(fieldMeta, "planned_classrooms")}>
                  <Input className={inputClassName} inputMode="numeric" {...form.register("planned_classrooms")} />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "planned_laboratories")}>
                  <Input className={inputClassName} inputMode="numeric" {...form.register("planned_laboratories")} />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "hostel_blocks_planned")}>
                  <Input className={inputClassName} inputMode="numeric" {...form.register("hostel_blocks_planned")} />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "library_branches_planned")}>
                  <Input
                    className={inputClassName}
                    inputMode="numeric"
                    {...form.register("library_branches_planned")}
                  />
                </FormField>
                <FormField meta={metaFor(fieldMeta, "facilities_notes")}>
                  <textarea
                    className="min-h-[100px] w-full rounded-md border border-[#dce3ec] px-3 py-2 text-[13px]"
                    {...form.register("facilities_notes")}
                  />
                </FormField>
              </div>
            ) : null}

            {activeStep === "review" ? (
              <div className="space-y-1">
                <ReviewRow label="Campus code" value={v.campus_code} />
                <ReviewRow label="Name" value={v.name} />
                <ReviewRow label="Main campus" value={v.is_main === "true" ? "Yes" : "No"} />
                <ReviewRow
                  label="Address"
                  value={[v.address_line1, v.city, v.state, v.country].filter(Boolean).join(", ")}
                />
                <ReviewRow label="Email" value={v.contact_email} />
                <ReviewRow label="Phone" value={v.contact_phone} />
                <ReviewRow label="Area (acres)" value={v.area_acres} />
                <ReviewRow label="Buildings" value={v.buildings_count} />
                <ReviewRow label="Facilities notes" value={v.facilities_notes} />
              </div>
            ) : null}

            <div className="mt-6 flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] pt-4">
              <button
                type="button"
                disabled={isBusy || activeStep === STEP_ORDER[0]}
                onClick={handleBackStep}
                className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
              >
                {data.back_step_label}
              </button>
              <div className="flex gap-2">
                {isLast ? (
                  <button
                    type="button"
                    disabled={isBusy}
                    onClick={() => void handleFinish()}
                    className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
                  >
                    <CheckIcon className="size-3.5" aria-hidden />
                    {data.create_label}
                  </button>
                ) : (
                  <button
                    type="button"
                    disabled={isBusy}
                    onClick={() => void handleContinue()}
                    className="inline-flex h-9 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
                  >
                    {data.next_label}
                  </button>
                )}
              </div>
            </div>
          </Section>
        ) : null}
      </QueryState>
    </div>
  );
}