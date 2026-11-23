import Link from "next/link";

import { CollegeAdminOutlineLink, CollegeAdminPrimaryLink } from "@/features/college-admin/components/ui/college-admin-page-buttons";
import type { OrganizationModuleEmptyState } from "@/features/college-admin/types/organization-module";
import { cn } from "@/lib/utils";

export function OrganizationSetupEmptyState({
  state,
  embedded = false,
}: {
  state: OrganizationModuleEmptyState;
  embedded?: boolean;
}) {
  return (
    <section
      className={cn(
        embedded
          ? "bg-transparent px-5 py-10 sm:px-8"
          : "overflow-hidden rounded-xl border border-[#e8ecf2] bg-white px-6 py-12 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:px-10 sm:py-14",
      )}
      data-testid="organization-setup-empty-state"
    >
      <div className="mx-auto max-w-lg text-center">
        <h3 className="text-[18px] font-semibold tracking-[-0.02em] text-[#111827]">{state.title}</h3>
        <p className="mt-2 text-[14px] leading-relaxed text-[#6b7280]">{state.description}</p>
      </div>
      {state.highlights.length ? (
        <div className="mx-auto mt-10 max-w-md">
          <p className="mb-3 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-[#9ca3af]">
            What you&apos;ll manage here
          </p>
          <ul className="space-y-2.5 rounded-lg border border-[#e8ecf2] bg-[#f8fafc] px-5 py-4 text-left text-[13px] leading-snug text-[#374151]">
            {state.highlights.map((item) => (
              <li key={item} className="flex gap-2.5">
                <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-[#245dd8]" aria-hidden />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <div className="mt-10 flex flex-wrap items-center justify-center gap-2">
        <CollegeAdminPrimaryLink href={state.primary_href}>{state.primary_label}</CollegeAdminPrimaryLink>
        {state.secondary_label && state.secondary_href ? (
          <CollegeAdminOutlineLink href={state.secondary_href}>{state.secondary_label}</CollegeAdminOutlineLink>
        ) : null}
      </div>
    </section>
  );
}

/** Inline empty hint for table areas when the page still has side panels. */
export function OrganizationTableEmptyHint({
  message,
  actionLabel,
  actionHref,
}: {
  message: string;
  actionLabel: string;
  actionHref: string;
}) {
  return (
    <div className="px-5 py-10 text-center">
      <p className="text-sm text-[#6b7280]">{message}</p>
      <Link href={actionHref} className="mt-3 inline-block text-[13px] font-medium text-[#245dd8] hover:underline">
        {actionLabel} →
      </Link>
    </div>
  );
}