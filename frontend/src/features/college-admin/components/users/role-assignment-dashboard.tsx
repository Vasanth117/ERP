"use client";
import { CollegeAdminModulePageHeading } from "@/features/college-admin/components/layout/college-admin-module-page-heading";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { ClockIcon } from "@/components/icons/erp/generated/clock";
import { InfoIcon } from "@/components/icons/erp/generated/info";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useRoleAssignmentPage,
  useSubmitRoleAssignment,
} from "@/features/college-admin/hooks/use-role-assignment";
import type { RoleAssignmentFormValues } from "@/features/college-admin/types/role-assignment";
import type { InstitutionFieldMeta } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function metaFor(fieldMeta: InstitutionFieldMeta[], key: string) {
  return fieldMeta.find((row) => row.key === key);
}

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
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

export function RoleAssignmentDashboard() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const userId = useMemo(
    () => searchParams.get("userId") ?? searchParams.get("user_id") ?? null,
    [searchParams],
  );
  const roleId = useMemo(
    () => searchParams.get("roleId") ?? searchParams.get("role_id") ?? null,
    [searchParams],
  );

  const pageQuery = useRoleAssignmentPage(userId, roleId);
  const submitMutation = useSubmitRoleAssignment(userId, roleId);

  const form = useForm<RoleAssignmentFormValues>({
    values: pageQuery.data?.form,
  });

  const watchedUser = form.watch("user_id");
  const watchedRole = form.watch("institution_role_id");

  useEffect(() => {
    if (!watchedUser || watchedUser === userId) return;
    const qs = new URLSearchParams();
    qs.set("userId", watchedUser);
    if (watchedRole) qs.set("roleId", watchedRole);
    else if (roleId) qs.set("roleId", roleId);
    router.replace(`/college-admin/users/role-assignment?${qs.toString()}`);
  }, [watchedUser, userId, watchedRole, roleId, router]);

  const data = pageQuery.data;

  const approvalNotice = useMemo(() => {
    if (!data) return null;
    const role = data.role_options.find((opt) => opt.value === watchedRole);
    return role?.approval_notice ?? data.approval_notice;
  }, [data, watchedRole]);

  const submitLabel = useMemo(() => {
    if (!data) return "Save";
    const role = data.role_options.find((opt) => opt.value === watchedRole);
    if (role?.requires_approval) return data.submit_label;
    return data.submit_direct_label;
  }, [data, watchedRole]);

  const onSubmit = form.handleSubmit((values) => {
    if (!data?.can_submit) {
      toast.error("You cannot assign roles");
      return;
    }
    submitMutation.mutate(values, {
      onSuccess: (result) => {
        toast.success(result.message);
        form.reset(result.page.form);
        const qs = new URLSearchParams();
        if (result.page.form.user_id) qs.set("userId", result.page.form.user_id);
        if (result.page.form.institution_role_id) qs.set("roleId", result.page.form.institution_role_id);
        router.replace(`/college-admin/users/role-assignment?${qs.toString()}`);
      },
      onError: onCollegeAdminMutationError,
    });
  });

  const focusForm = useCallback(() => {
    document.getElementById("role-assignment-form")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  const isBusy = submitMutation.isPending;
  const fieldMeta = data?.form_field_meta ?? [];

  return (
    <div className="space-y-5" data-figma-frame="69:127288">
      <CollegeAdminModulePageHeading title={data?.page_title ?? "Role Assignment"} subtitle={data?.page_subtitle} actions={<><Link
            href={data?.assignment_history_href ?? "/college-admin/users/user-access-history"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            <ClockIcon className="size-3.5" aria-hidden />
            {data?.assignment_history_label ?? "Assignment history"}
          </Link>
          <button
            type="button"
            onClick={focusForm}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1d4ed8]"
          >
            <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={data?.assign_role_label ?? "Assign role" } />
          </button></>} />

      <QueryState query={pageQuery}>
        {data ? (
          <div className="grid gap-5 lg:grid-cols-3">
            <form id="role-assignment-form" className="space-y-5 lg:col-span-2" onSubmit={(e) => void onSubmit(e)}>
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.form_section_title}</h3>
                </div>
                <div className="grid gap-4 px-5 py-4 sm:grid-cols-2">
                  <FormField meta={metaFor(fieldMeta, "user_id")}>
                    <select
                      {...form.register("user_id", { required: true })}
                      disabled={isBusy}
                      className="h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#111827]"
                    >
                      <option value="">Select user</option>
                      {data.user_options.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </FormField>
                  <FormField meta={metaFor(fieldMeta, "institution_role_id")}>
                    <select
                      {...form.register("institution_role_id", { required: true })}
                      disabled={isBusy}
                      className="h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#111827]"
                    >
                      <option value="">Select role</option>
                      {data.role_options.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </FormField>
                  <FormField meta={metaFor(fieldMeta, "scope_key")}>
                    <select
                      {...form.register("scope_key", { required: true })}
                      disabled={isBusy}
                      className="h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#111827] sm:col-span-2"
                    >
                      {data.scope_options.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </FormField>
                  <FormField meta={metaFor(fieldMeta, "valid_from")}>
                    <input
                      type="date"
                      {...form.register("valid_from", { required: true })}
                      disabled={isBusy}
                      className="h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#111827]"
                    />
                  </FormField>
                  <FormField meta={metaFor(fieldMeta, "valid_until")}>
                    <input
                      type="date"
                      {...form.register("valid_until")}
                      disabled={isBusy}
                      className="h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#111827]"
                    />
                  </FormField>
                  <div className="sm:col-span-2">
                    <FormField meta={metaFor(fieldMeta, "reason")}>
                      <textarea
                        {...form.register("reason")}
                        disabled={isBusy}
                        rows={3}
                        placeholder="Acting HoD until regular appointment"
                        className="w-full rounded-md border border-[#dce3ec] bg-white px-3 py-2 text-[13px] text-[#111827]"
                      />
                    </FormField>
                  </div>
                </div>
              </section>

              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.recent_section_title}</h3>
                </div>
                {data.recent_rows.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[40rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {data.recent_table_headers.map((header, index) => (
                            <th key={header} className={cn("pb-3 font-medium", index === 0 ? "px-5" : "pr-3")}>
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {data.recent_rows.map((row, index) => (
                          <tr key={`${row.user_name}-${row.role_name}-${index}`} className="border-t border-[#f1f5f9]">
                            <td className="px-5 py-3 text-[#111827]">{row.user_name}</td>
                            <td className="py-3 pr-3 text-[#374151]">{row.role_name}</td>
                            <td className="py-3 pr-3 text-[#6b7280]">{row.scope_label}</td>
                            <td className="py-3 pr-3 text-[#6b7280]">{row.until_label}</td>
                            <td className="py-3 pr-3">
                              <StatusPill label={row.status_label} tone={row.status_tone} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-6 text-sm text-[#9ca3af]">No assignments yet.</p>
                )}
                <div className="border-t border-[#f1f5f9] px-5 py-3">
                  <Link href={data.view_history_href} className="text-[12px] font-medium text-[#245dd8] hover:underline">
                    {data.view_history_label} →
                  </Link>
                </div>
              </section>
            </form>

            <aside className="space-y-4">
              {approvalNotice ? (
                <div className="flex gap-3 rounded-xl border border-[#bfdbfe] bg-[#eff6ff] px-4 py-3.5">
                  <InfoIcon className="mt-0.5 size-4 shrink-0 text-[#2563eb]" aria-hidden />
                  <p className="text-[12px] leading-relaxed text-[#1e40af]">{approvalNotice}</p>
                </div>
              ) : null}

              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.current_roles_section_title}</h3>
                </div>
                <ul className="divide-y divide-[#f1f5f9] px-5 py-2">
                  {data.current_roles.map((card) => (
                    <li key={`${card.role_name}-${card.detail_line}`} className="py-3">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-[13px] font-medium text-[#111827]">{card.role_name}</p>
                        <StatusPill label={card.status_label} tone={card.status_tone} />
                      </div>
                      <p className="mt-1 text-[11px] text-[#6b7280]">{card.detail_line}</p>
                    </li>
                  ))}
                </ul>
              </section>
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
              disabled={!data.can_submit || isBusy}
              onClick={() => void onSubmit()}
              className="inline-flex h-9 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1d4ed8] disabled:opacity-50"
            >
              {submitLabel}
            </button>
          </div>
        </footer>
      ) : null}
    </div>
  );
}