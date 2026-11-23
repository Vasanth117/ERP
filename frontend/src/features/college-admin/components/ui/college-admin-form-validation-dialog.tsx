"use client";

import Link from "next/link";
import { useCallback, useEffect, useId } from "react";
import { createPortal } from "react-dom";

import { TriangleAlertIcon } from "@/components/icons/erp/generated/triangle-alert";
import { XIcon } from "@/components/icons/erp/generated/x";
import {
  CollegeAdminOutlineButton,
  CollegeAdminPrimaryButton,
} from "@/features/college-admin/components/ui/college-admin-page-buttons";
import {
  scrollToFormField,
  type FormValidationDetail,
} from "@/lib/api/form-validation";

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

export function CollegeAdminFormValidationDialog({
  open,
  title,
  description,
  items,
  onClose,
}: {
  open: boolean;
  title: string;
  description: string;
  items: FormValidationDetail[];
  onClose: () => void;
}) {
  const titleId = useId();
  const descId = useId();
  useBodyScrollLock(open);

  const onKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    },
    [onClose],
  );

  useEffect(() => {
    if (!open) return;
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onKeyDown]);

  if (!open || typeof document === "undefined") return null;

  const firstScrollable = items.find((item) => item.action_type === "scroll");

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-[#0f172a]/40 backdrop-blur-[1px]"
        aria-label="Close dialog"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descId}
        className="relative z-10 flex max-h-[min(90vh,640px)] w-full max-w-lg flex-col overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_20px_50px_rgba(15,23,42,0.18)]"
      >
        <div className="flex items-start gap-3 border-b border-[#f1f5f9] px-5 py-4">
          <span className="mt-0.5 inline-flex size-9 shrink-0 items-center justify-center rounded-full bg-[#fef2f2] text-[#dc2626]">
            <TriangleAlertIcon className="size-4" aria-hidden />
          </span>
          <p className="min-w-0 flex-1">
            <span id={titleId} className="block text-[16px] font-semibold text-[#111827]">
              {title}
            </span>
            <span id={descId} className="mt-1 block text-[13px] leading-relaxed text-[#6b7280]">
              {description}
            </span>
          </p>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex size-8 shrink-0 items-center justify-center rounded-md text-[#6b7280] hover:bg-[#f3f4f6]"
            aria-label="Close"
          >
            <XIcon className="size-4" />
          </button>
        </div>
        <ul className="max-h-[50vh] space-y-3 overflow-y-auto px-5 py-4">
          {items.map((item) => (
            <li key={item.field_key} className="rounded-lg border border-[#f1f5f9] bg-[#f8fafc] px-4 py-3">
              <p className="text-[13px] font-semibold text-[#111827]">{item.label}</p>
              <p className="mt-1 text-[12px] leading-relaxed text-[#6b7280]">{item.message}</p>
              <div className="mt-3">
                {item.action_type === "navigate" && item.action_href ? (
                  <Link
                    href={item.action_href}
                    className="inline-flex h-8 items-center rounded-md bg-[#245dd8] px-3 text-[12px] font-medium text-white hover:bg-[#1f4fb8]"
                    onClick={onClose}
                  >
                    {item.action_label}
                  </Link>
                ) : (
                  <button
                    type="button"
                    className="inline-flex h-8 items-center rounded-md border border-[#dce3ec] bg-white px-3 text-[12px] font-medium text-[#374151] hover:bg-[#f9fafb]"
                    onClick={() => {
                      scrollToFormField(item.field_key);
                      onClose();
                    }}
                  >
                    {item.action_label}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
        <div className="flex justify-end border-t border-[#f1f5f9] px-5 py-3">
          <CollegeAdminOutlineButton onClick={onClose}>Close</CollegeAdminOutlineButton>
          {firstScrollable ? (
            <CollegeAdminPrimaryButton
              className="ml-2"
              onClick={() => {
                scrollToFormField(firstScrollable.field_key);
                onClose();
              }}
            >
              {firstScrollable.action_label}
            </CollegeAdminPrimaryButton>
          ) : null}
        </div>
      </div>
    </div>,
    document.body,
  );
}