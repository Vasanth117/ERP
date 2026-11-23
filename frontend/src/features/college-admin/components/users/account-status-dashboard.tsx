"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { BanIcon } from "@/components/icons/erp/generated/ban";
import { DatabaseIcon } from "@/components/icons/erp/generated/database";
import { LockIcon } from "@/components/icons/erp/generated/lock";
import { MailIcon } from "@/components/icons/erp/generated/mail";
import { SearchIcon } from "@/components/icons/erp/generated/search";
import { Label } from "@/components/ui/label";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { CollegeAdminSectionNav } from "@/features/college-admin/components/ui/college-admin-section-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAccountStatusPage,
  useDownloadAccountStatus,
  useSubmitAccountSuspension,
} from "@/features/college-admin/hooks/use-account-status";
import type {
  AccountStatusInfoCard,
  AccountStatusSuspendFormValues,
} from "@/features/college-admin/types/account-status";
import type { InstitutionFieldMeta } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function metaFor(fieldMeta: InstitutionFieldMeta[], key: string) {
  return fieldMeta.find((row) => row.key === key);
}

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    purple: "bg-[#f5f3ff] text-[#6d28d9]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    info: "bg-[#3b82f6]",
    purple: "bg-[#8b5cf6]",
    error: "bg-[#ef4444]",
    muted: "bg-[#9ca3af]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}

function WhatHappensIcon({ iconKey }: { iconKey: string }) {
  if (iconKey === "database") return <DatabaseIcon className="size-4 text-[#6b7280]" />;
  if (iconKey === "mail") return <MailIcon className="size-4 text-[#6b7280]" />;
  return <LockIcon className="size-4 text-[#6b7280]" />;
}

function InfoCardList({ title, cards }: { title: string; cards: AccountStatusInfoCard[] }) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="border-b border-[#f1f5f9] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
      </div>
      <ul className="divide-y divide-[#f1f5f9] px-5 py-1">
        {cards.map((card) => (
          <li key={card.key} className="flex gap-3 py-3">
            <span className="mt-0.5 flex size-8 items-center justify-center rounded-lg bg-[#f9fafb]">
              <WhatHappensIcon iconKey={card.icon_key} />
            </span>
            <div>
              <p className="text-[13px] font-medium text-[#111827]">{card.title}</p>
              <p className="text-[11px] text-[#6b7280]">{card.description}</p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function AccountStatusDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialTab = searchParams.get("tab") ?? "suspended";
  const userId = searchParams.get("userId") ?? searchParams.get("user_id") ?? null;

  const [tab, setTab] = useState(initialTab);
  const [page, setPage] = useState(1);

  const pageQuery = useAccountStatusPage(tab, page, userId);
  const submitMutation = useSubmitAccountSuspension(tab, page, userId);
  const downloadMutation = useDownloadAccountStatus(tab);

  const form = useForm<AccountStatusSuspendFormValues>({
    values: pageQuery.data?.suspend_form,
  });

  const data = pageQuery.data;

  useEffect(() => {
    if (data?.active_tab && data.active_tab !== tab) {
      setTab(data.active_tab);
    }
  }, [data?.active_tab, tab]);

  const switchTab = useCallback(
    (next: string) => {
      setTab(next);
      setPage(1);
      const qs = new URLSearchParams();
      qs.set("tab", next);
      if (userId) qs.set("userId", userId);
      router.replace(`/college-admin/users/user-account-activation-suspension?${qs.toString()}`);
    },
    [router, userId],
  );

  const onSuspend = form.handleSubmit((values) => {
    if (!data?.can_suspend) {
      toast.error("You cannot suspend accounts");
      return;
    }
    submitMutation.mutate(values, {
      onSuccess: (result) => {
        toast.success(result.message);
        setTab("suspended");
        setPage(1);
        router.replace("/college-admin/users/user-account-activation-suspension?tab=suspended");
        form.reset(result.page.suspend_form);
      },
      onError: onCollegeAdminMutationError,
    });
  });

  const isBusy = submitMutation.isPending || downloadMutation.isPending;
  const fieldMeta = data?.suspend_field_meta ?? [];

  return (
    <div className="space-y-5" data-figma-frame="69:127501">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "User Account Activation / Suspension"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            disabled={!data || isBusy}
            onClick={() =>
              downloadMutation.mutate(undefined, {
                onError: onCollegeAdminMutationError,
              })
            }
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
          >
            <CollegeAdminDownload className="size-3.5" aria-hidden />
            {data?.export_label ?? "Export"}
          </button>
          <button
            type="button"
            onClick={() => document.getElementById("suspend-account-form")?.scrollIntoView({ behavior: "smooth" })}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#dc2626] px-4 text-xs font-medium text-white hover:bg-[#b91c1c]"
          >
            <BanIcon className="size-3.5" aria-hidden />
            {data?.suspend_account_label ?? "Suspend account"}
          </button>
        </div>
      </div>

      <QueryState query={pageQuery}>
        {data ? (
          <div className="grid gap-5 lg:grid-cols-3">
            <div className="space-y-4 lg:col-span-2">
              <CollegeAdminSectionNav
                items={data.tabs.map((t) => ({
                  key: t.key,
                  label: `${t.label} (${t.count})`,
                  active: t.active,
                }))}
                onSelect={switchTab}
              />

              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                {data.table_rows.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[40rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {data.table_headers.map((header, index) => (
                            <th key={header} className={cn("pb-3 font-medium", index === 0 ? "px-5" : "pr-3")}>
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {data.table_rows.map((row) => (
                          <tr key={row.user_id} className="border-t border-[#f1f5f9]">
                            <td className="px-5 py-3">
                              <Link href={row.detail_href} className="font-medium text-[#111827] hover:text-[#245dd8]">
                                {row.user_name}
                              </Link>
                            </td>
                            {data.active_tab === "pending_activation" ? (
                              <>
                                <td className="py-3 pr-3 text-[#374151]">{row.role_label}</td>
                                <td className="py-3 pr-3 text-[#6b7280]">{row.since_label}</td>
                                <td className="py-3 pr-3 text-[#6b7280]">{row.department_label}</td>
                                <td className="py-3 pr-3">
                                  <StatusPill label={row.review_label} tone={row.review_tone} />
                                </td>
                              </>
                            ) : (
                              <>
                                <td className="py-3 pr-3 text-[#374151]">{row.role_label}</td>
                                <td className="py-3 pr-3 text-[#6b7280]">{row.reason_label}</td>
                                <td className="py-3 pr-3 text-[#6b7280]">{row.since_label}</td>
                                <td className="py-3 pr-3">
                                  <StatusPill label={row.review_label} tone={row.review_tone} />
                                </td>
                              </>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-8 text-sm text-[#9ca3af]">No accounts in this tab yet.</p>
                )}

                <div className="flex flex-col gap-3 border-t border-[#f1f5f9] px-5 py-3 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-[12px] text-[#6b7280]">{data.table_footer_label}</p>
                  {data.pagination.total_pages > 1 ? (
                    <MotionPager page={page} setPage={setPage} pagination={data.pagination} />
                  ) : null}
                </div>
              </section>
            </div>

            <aside className="space-y-4">
              <form
                id="suspend-account-form"
                className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]"
                onSubmit={(e) => void onSuspend(e)}
              >
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.suspend_form_section_title}</h3>
                </div>
                <div className="space-y-4 px-5 py-4">
                  <FormField meta={metaFor(fieldMeta, "user_id")}>
                    <div className="relative">
                      <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-[#9ca3af]" />
                      <select
                        {...form.register("user_id", { required: true })}
                        disabled={isBusy || !data.can_suspend}
                        className="h-9 w-full rounded-md border border-[#dce3ec] bg-white pl-9 pr-3 text-[13px] text-[#111827]"
                      >
                        <option value="">Search user…</option>
                        {data.user_options.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </FormField>
                  <FormField meta={metaFor(fieldMeta, "reason_code")}>
                    <select
                      {...form.register("reason_code", { required: true })}
                      disabled={isBusy || !data.can_suspend}
                      className="h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
                    >
                      {data.reason_options.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </FormField>
                  <FormField meta={metaFor(fieldMeta, "effective_from")}>
                    <input
                      type="date"
                      {...form.register("effective_from", { required: true })}
                      disabled={isBusy || !data.can_suspend}
                      className="h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
                    />
                  </FormField>
                  <FormField meta={metaFor(fieldMeta, "review_date")}>
                    <input
                      type="date"
                      {...form.register("review_date")}
                      disabled={isBusy || !data.can_suspend}
                      className="h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
                    />
                  </FormField>
                  <FormField meta={metaFor(fieldMeta, "notes")}>
                    <textarea
                      {...form.register("notes", { required: true })}
                      disabled={isBusy || !data.can_suspend}
                      rows={3}
                      placeholder="Add details for the audit record"
                      className="w-full rounded-md border border-[#dce3ec] bg-white px-3 py-2 text-[13px]"
                    />
                  </FormField>
                </div>
              </form>

              <InfoCardList title={data.what_happens_title} cards={data.what_happens_cards} />
            </aside>
          </div>
        ) : null}
      </QueryState>

      {data ? (
        <footer className="sticky bottom-0 z-10 -mx-1 flex flex-col gap-3 border-t border-[#e8ecf2] bg-[#f5f7fa]/95 px-1 py-4 backdrop-blur sm:flex-row sm:items-center sm:justify-between">
          <p className="text-[12px] text-[#6b7280]">{data.footer_note}</p>
          <div className="flex gap-2">
            <Link
              href={data.cancel_href}
              className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
            >
              {data.cancel_label}
            </Link>
            <button
              type="button"
              disabled={!data.can_suspend || isBusy}
              onClick={() => void onSuspend()}
              className="inline-flex h-9 items-center rounded-md bg-[#dc2626] px-4 text-xs font-medium text-white hover:bg-[#b91c1c] disabled:opacity-50"
            >
              {data.submit_suspend_label}
            </button>
          </div>
        </footer>
      ) : null}
    </div>
  );
}

function FormField({ meta, children }: { meta?: InstitutionFieldMeta; children: React.ReactNode }) {
  if (!meta) return null;
  return (
    <div className="space-y-1.5">
      <Label className="text-[13px] font-medium text-[#374151]">
        {meta.label}
        {meta.required ? <span className="text-[#dc2626]"> *</span> : null}
      </Label>
      {children}
    </div>
  );
}

function MotionPager({
  page,
  setPage,
  pagination,
}: {
  page: number;
  setPage: (n: number) => void;
  pagination: {
    page_numbers: number[];
    has_previous: boolean;
    has_next: boolean;
    page: number;
  };
}) {
  return (
    <div className="flex items-center gap-1 text-[12px]">
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
        disabled={!pagination.has_previous}
        onClick={() => setPage(Math.max(1, page - 1))}
      >
        Previous
      </button>
      {pagination.page_numbers.map((num, index) =>
        num === -1 ? (
          <span key={`e-${index}`} className="px-1">
            …
          </span>
        ) : (
          <button
            key={num}
            type="button"
            className={cn(
              "min-w-8 rounded border px-2 py-1 tabular-nums",
              num === pagination.page ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]" : "border-[#dce3ec]",
            )}
            onClick={() => setPage(num)}
          >
            {num}
          </button>
        ),
      )}
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
        disabled={!pagination.has_next}
        onClick={() => setPage(page + 1)}
      >
        Next
      </button>
    </div>
  );
}