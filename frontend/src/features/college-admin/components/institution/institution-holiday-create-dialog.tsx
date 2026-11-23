"use client";

import { useCallback, useEffect, useId, type FormEvent } from "react";
import { createPortal } from "react-dom";

import { XIcon } from "@/components/icons/erp/generated/x";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { InstitutionCalendarSettingsPage } from "@/features/college-admin/types/institution";

const selectClass =
  "h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#111827]";

function useBodyScrollLock(locked: boolean) {
  useEffect(() => {
    if (!locked) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [locked]);
}

export type HolidayCreateFormState = {
  title: string;
  start_date: string;
  end_date: string;
  holiday_type: string;
  applies_to: string;
};

const EMPTY_FORM: HolidayCreateFormState = {
  title: "",
  start_date: "",
  end_date: "",
  holiday_type: "institution",
  applies_to: "all",
};

export function defaultHolidayCreateForm(page?: InstitutionCalendarSettingsPage): HolidayCreateFormState {
  return {
    ...EMPTY_FORM,
    holiday_type: page?.create_holiday_type_options?.[0]?.value ?? "institution",
    applies_to: page?.create_holiday_applies_options?.[0]?.value ?? "all",
  };
}

export function InstitutionHolidayCreateDialog({
  open,
  onClose,
  page,
  form,
  onChange,
  onSubmit,
  isSubmitting,
  academicYearLabel,
}: {
  open: boolean;
  onClose: () => void;
  page: InstitutionCalendarSettingsPage;
  form: HolidayCreateFormState;
  onChange: (patch: Partial<HolidayCreateFormState>) => void;
  onSubmit: () => void;
  isSubmitting: boolean;
  academicYearLabel?: string;
}) {
  const titleId = useId();
  useBodyScrollLock(open);

  const onKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === "Escape" && !isSubmitting) onClose();
    },
    [isSubmitting, onClose],
  );

  useEffect(() => {
    if (!open) return;
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onKeyDown]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit();
  };

  if (!open || typeof document === "undefined") return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-[#0f172a]/45 p-4 backdrop-blur-[2px]"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="flex max-h-[min(90vh,640px)] w-full max-w-lg flex-col overflow-hidden rounded-2xl border border-[#e2e8f0] bg-white shadow-[0_24px_48px_rgba(15,23,42,0.18)]"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b border-[#f1f5f9] px-6 py-4">
          <div>
            <h2 id={titleId} className="text-[17px] font-semibold text-[#111827]">
              {page.add_holiday_dialog_title ?? "Add holiday"}
            </h2>
            <p className="mt-1 text-[13px] text-[#6b7280]">
              {page.add_holiday_dialog_subtitle ?? "Register a holiday"}
              {academicYearLabel ? (
                <span className="block text-[12px] text-[#9ca3af]">Academic year: {academicYearLabel}</span>
              ) : null}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="rounded-md p-1 text-[#6b7280] hover:bg-[#f3f4f6] disabled:opacity-50"
            aria-label="Close"
          >
            <XIcon className="size-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col overflow-y-auto">
          <div className="grid gap-4 px-6 py-5">
            <div className="space-y-1.5">
              <Label className="text-[13px] font-medium text-[#374151]">
                Holiday name <span className="text-[#dc2626]">*</span>
              </Label>
              <Input
                className="h-9 border-[#dce3ec] text-[13px]"
                value={form.title}
                onChange={(e) => onChange({ title: e.target.value })}
                placeholder="e.g. Pongal / Republic Day"
                required
                autoFocus
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label className="text-[13px] font-medium text-[#374151]">
                  Start date <span className="text-[#dc2626]">*</span>
                </Label>
                <Input
                  className="h-9 border-[#dce3ec] text-[13px]"
                  type="date"
                  value={form.start_date}
                  onChange={(e) => onChange({ start_date: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-[13px] font-medium text-[#374151]">End date</Label>
                <Input
                  className="h-9 border-[#dce3ec] text-[13px]"
                  type="date"
                  value={form.end_date}
                  onChange={(e) => onChange({ end_date: e.target.value })}
                />
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label className="text-[13px] font-medium text-[#374151]">Type</Label>
                <select
                  className={selectClass}
                  value={form.holiday_type}
                  onChange={(e) => onChange({ holiday_type: e.target.value })}
                >
                  {(page.create_holiday_type_options ?? []).map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-[13px] font-medium text-[#374151]">Applies to</Label>
                <select
                  className={selectClass}
                  value={form.applies_to}
                  onChange={(e) => onChange({ applies_to: e.target.value })}
                >
                  {(page.create_holiday_applies_options ?? []).map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="mt-auto flex justify-end gap-2 border-t border-[#f1f5f9] px-6 py-4">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
            >
              {page.create_holiday_cancel_label ?? "Cancel"}
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !form.title.trim() || !form.start_date}
              className="inline-flex h-9 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
            >
              {isSubmitting ? "Saving…" : page.create_holiday_save_label ?? "Add holiday"}
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body,
  );
}