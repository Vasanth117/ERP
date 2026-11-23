"use client";

import { useCallback, useEffect, useId, type FormEvent } from "react";
import { createPortal } from "react-dom";

import { XIcon } from "@/components/icons/erp/generated/x";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { InstitutionPoliciesPage } from "@/features/college-admin/types/institution";

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

export type PolicyCreateFormState = {
  title: string;
  category: string;
  audience: string;
  version_label: string;
  effective_from: string;
  status: string;
  owner_label: string;
  approved_by_label: string;
  acknowledgement_requirement: string;
};

const EMPTY_FORM: PolicyCreateFormState = {
  title: "",
  category: "Academic",
  audience: "all",
  version_label: "1.0",
  effective_from: "",
  status: "draft",
  owner_label: "",
  approved_by_label: "",
  acknowledgement_requirement: "",
};

export function InstitutionPolicyCreateDialog({
  open,
  onClose,
  page,
  form,
  onChange,
  onSubmit,
  isSubmitting,
}: {
  open: boolean;
  onClose: () => void;
  page: InstitutionPoliciesPage;
  form: PolicyCreateFormState;
  onChange: (patch: Partial<PolicyCreateFormState>) => void;
  onSubmit: () => void;
  isSubmitting: boolean;
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
        className="flex max-h-[min(90vh,720px)] w-full max-w-xl flex-col overflow-hidden rounded-2xl border border-[#e2e8f0] bg-white shadow-[0_24px_48px_rgba(15,23,42,0.18)]"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b border-[#f1f5f9] px-6 py-4">
          <div>
            <h2 id={titleId} className="text-[17px] font-semibold text-[#111827]">
              {page.create_dialog_title ?? "Add policy"}
            </h2>
            <p className="mt-1 text-[13px] text-[#6b7280]">
              {page.create_dialog_subtitle ?? "Register a new institutional policy"}
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
          <div className="grid gap-4 px-6 py-5 sm:grid-cols-2">
            <div className="space-y-1.5 sm:col-span-2" data-field-key="title">
              <Label className="text-[13px] font-medium text-[#374151]">
                Policy title <span className="text-[#dc2626]">*</span>
              </Label>
              <Input
                className="h-9 border-[#dce3ec] text-[13px]"
                value={form.title}
                onChange={(e) => onChange({ title: e.target.value })}
                placeholder="e.g. Student code of conduct"
                required
                autoFocus
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-[13px] font-medium text-[#374151]">Category</Label>
              <select
                className={selectClass}
                value={form.category}
                onChange={(e) => onChange({ category: e.target.value })}
              >
                {(page.create_category_options ?? []).map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-[13px] font-medium text-[#374151]">Audience</Label>
              <select
                className={selectClass}
                value={form.audience}
                onChange={(e) => onChange({ audience: e.target.value })}
              >
                {(page.create_audience_options ?? []).map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-[13px] font-medium text-[#374151]">Version</Label>
              <Input
                className="h-9 border-[#dce3ec] text-[13px]"
                value={form.version_label}
                onChange={(e) => onChange({ version_label: e.target.value })}
                placeholder="1.0"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-[13px] font-medium text-[#374151]">Effective from</Label>
              <Input
                className="h-9 border-[#dce3ec] text-[13px]"
                type="date"
                value={form.effective_from}
                onChange={(e) => onChange({ effective_from: e.target.value })}
              />
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label className="text-[13px] font-medium text-[#374151]">Status</Label>
              <select
                className={selectClass}
                value={form.status}
                onChange={(e) => onChange({ status: e.target.value })}
              >
                {(page.create_status_options ?? []).map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label className="text-[13px] font-medium text-[#374151]">Policy owner</Label>
              <Input
                className="h-9 border-[#dce3ec] text-[13px]"
                value={form.owner_label}
                onChange={(e) => onChange({ owner_label: e.target.value })}
                placeholder="e.g. Dean of Academic Affairs"
              />
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label className="text-[13px] font-medium text-[#374151]">Approved by</Label>
              <Input
                className="h-9 border-[#dce3ec] text-[13px]"
                value={form.approved_by_label}
                onChange={(e) => onChange({ approved_by_label: e.target.value })}
                placeholder="e.g. Academic council, 2024"
              />
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label className="text-[13px] font-medium text-[#374151]">Acknowledgement requirement</Label>
              <textarea
                className="min-h-[80px] w-full rounded-md border border-[#dce3ec] px-3 py-2 text-[13px]"
                value={form.acknowledgement_requirement}
                onChange={(e) => onChange({ acknowledgement_requirement: e.target.value })}
                placeholder="Who must acknowledge this policy and by when"
              />
            </div>
          </div>

          <div className="mt-auto flex justify-end gap-2 border-t border-[#f1f5f9] px-6 py-4">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
            >
              {page.create_cancel_label ?? "Cancel"}
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !form.title.trim()}
              className="inline-flex h-9 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
            >
              {isSubmitting ? "Creating…" : page.create_save_label ?? "Create policy"}
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body,
  );
}

export function defaultPolicyCreateForm(page?: InstitutionPoliciesPage): PolicyCreateFormState {
  return {
    ...EMPTY_FORM,
    category: page?.create_category_options?.[0]?.value ?? "Academic",
    audience: page?.create_audience_options?.[0]?.value ?? "all",
    status: page?.create_status_options?.[0]?.value ?? "draft",
  };
}