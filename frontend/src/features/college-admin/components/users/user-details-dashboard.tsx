"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { BanIcon } from "@/components/icons/erp/generated/ban";
import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { ClockIcon } from "@/components/icons/erp/generated/clock";
import { KeyIcon } from "@/components/icons/erp/generated/key";
import { MailIcon } from "@/components/icons/erp/generated/mail";
import { PencilIcon } from "@/components/icons/erp/generated/pencil";
import { PhoneIcon } from "@/components/icons/erp/generated/phone";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useUserDetailsPage } from "@/features/college-admin/hooks/use-user-details";
import { resetUserAccess, suspendUser } from "@/features/college-admin/api/users";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import { cn } from "@/lib/utils";

function Badge({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    info: "bg-[#eef2ff] text-[#4338ca]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>{label}</span>
  );
}

function SectionCard({
  title,
  actionHref,
  actionLabel,
  children,
  footer,
}: {
  title: string;
  actionHref?: string;
  actionLabel?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="flex items-center justify-between gap-2 border-b border-[#f1f5f9] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
        {actionHref && actionLabel ? (
          <Link href={actionHref} className="text-[12px] font-medium text-[#245dd8] hover:underline">
            {actionLabel} →
          </Link>
        ) : null}
      </div>
      <div className="px-5 py-4">{children}</div>
      {footer ? <div className="border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">{footer}</div> : null}
    </section>
  );
}


export function UserDetailsDashboard() {
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const userId = useMemo(() => {
    return searchParams.get("userId") ?? searchParams.get("user_id") ?? "";
  }, [searchParams]);

  const { data, isLoading, isError, error, refetch } = useUserDetailsPage(userId || null);

  const resetMutation = useMutation({
    mutationFn: () => resetUserAccess(userId),
    onSuccess: (payload) => {
      toast.success("Password reset initiated");
      if (payload.reset_token) {
        toast.message("Dev reset token", { description: payload.reset_token });
      }
      void queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.userDetailsPage(userId) });
    },
    onError: () => toast.error("Could not reset access"),
  });

  const suspendMutation = useMutation({
    mutationFn: () => suspendUser(userId, "Suspended from user details"),
    onSuccess: () => {
      toast.success("User suspended");
      void queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.userDetailsPage(userId) });
      void refetch();
    },
    onError: () => toast.error("Could not suspend user"),
  });

  const handleSuspend = useCallback(() => {
    if (!data?.show_suspend_action) return;
    if (!window.confirm("Suspend this user account?")) return;
    suspendMutation.mutate();
  }, [data?.show_suspend_action, suspendMutation]);

  if (!userId) {
    return (
      <div className="rounded-xl border border-[#e8ecf2] bg-white p-8 text-center text-sm text-[#6b7280]">
        Select a user from{" "}
        <Link href="/college-admin/users/all-users-list" className="font-medium text-[#245dd8] hover:underline">
          All users
        </Link>{" "}
        to view their profile.
      </div>
    );
  }

  return (
    <div className="space-y-5" data-figma-frame="69:125470">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <Link
            href={data?.back_href ?? "/college-admin/users/all-users-list"}
            className="inline-flex items-center gap-1 text-[12px] font-medium text-[#245dd8] hover:underline"
          >
            <ChevronLeftIcon className="size-3.5" aria-hidden />
            {data?.back_label ?? "All users"}
          </Link>
          <h2 className="mt-2 text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "User Details"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            disabled={!data || resetMutation.isPending}
            onClick={() => resetMutation.mutate()}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
          >
            <KeyIcon className="size-3.5" aria-hidden />
            {data?.reset_password_label ?? "Reset password"}
          </button>
          {data?.show_suspend_action !== false ? (
            <button
              type="button"
              disabled={!data || suspendMutation.isPending}
              onClick={handleSuspend}
              className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
            >
              <BanIcon className="size-3.5" aria-hidden />
              {data?.suspend_label ?? "Suspend"}
            </button>
          ) : null}
          <Link
            href={data?.edit_user_href ?? "#"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <PencilIcon className="size-3.5" aria-hidden />
            {data?.edit_user_label ?? "Edit user"}
          </Link>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
                <div
                  className="flex size-14 shrink-0 items-center justify-center rounded-full bg-[#eff6ff] text-lg font-semibold text-[#245dd8]"
                  aria-hidden
                >
                  {data.profile_initials}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-[18px] font-semibold text-[#111827]">{data.profile_name}</h3>
                    {data.profile_badges.map((b) => (
                      <Badge key={b.key} label={b.label} tone={b.tone} />
                    ))}
                  </div>
                  <p className="mt-1 text-[13px] text-[#6b7280]">{data.designation_line}</p>
                  <div className="mt-3 flex flex-col gap-2 text-[13px] text-[#374151] sm:flex-row sm:flex-wrap sm:gap-4">
                    <span className="inline-flex items-center gap-1.5">
                      <MailIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                      {data.email}
                    </span>
                    <span className="inline-flex items-center gap-1.5">
                      <PhoneIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                      {data.phone_label}
                    </span>
                    <span className="inline-flex items-center gap-1.5">
                      <ClockIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                      {data.last_login_summary}
                    </span>
                  </div>
                </div>
              </div>
            </section>

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
              <div className="space-y-5">
                <SectionCard
                  title={data.account_section_title}
                  actionHref={data.account_edit_href}
                  actionLabel={data.account_edit_label}
                >
                  <dl className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
                    {data.account_fields.map((field) => (
                      <div key={field.key}>
                        <dt className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {field.label}
                        </dt>
                        <dd className="mt-1 text-[14px] text-[#111827]">
                          {field.tone ? (
                            <Badge label={field.value} tone={field.tone} />
                          ) : (
                            field.value
                          )}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </SectionCard>

                <SectionCard
                  title={data.roles_section_title}
                  actionHref={data.assign_role_href}
                  actionLabel={data.assign_role_label}
                  footer={
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span>{data.active_roles_footer_label}</span>
                      <Link href={data.role_assignment_href} className="font-medium text-[#245dd8] hover:underline">
                        {data.role_assignment_label} →
                      </Link>
                    </div>
                  }
                >
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[32rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {data.roles_table_headers.map((header) => (
                            <th key={header} className="pb-3 pr-4 font-medium">
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.assigned_roles.map((row, index) => (
                          <tr key={`${row.role_name}-${index}`}>
                            <td className="py-2.5 pr-4 font-medium text-[#111827]">{row.role_name}</td>
                            <td className="py-2.5 pr-4 text-[#374151]">{row.scope_label}</td>
                            <td className="py-2.5 pr-4 text-[#374151]">{row.assigned_by_label}</td>
                            <td className="py-2.5 pr-4 tabular-nums text-[#374151]">{row.since_label}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </SectionCard>
              </div>

              <div className="space-y-5">
                <SectionCard title={data.permissions_section_title}>
                  <ul className="space-y-4">
                    {data.permission_bars.map((bar) => (
                      <li key={bar.key}>
                        <div className="flex items-baseline justify-between gap-2">
                          <span className="text-[13px] font-medium text-[#111827]">{bar.label}</span>
                          <span className="text-[12px] text-[#6b7280]">{bar.description}</span>
                        </div>
                        <div className="mt-2 h-2 overflow-hidden rounded-full bg-[#f1f5f9]">
                          <div
                            className="h-full rounded-full bg-[#245dd8] transition-all"
                            style={{ width: `${Math.min(100, Math.max(0, bar.progress_percent))}%` }}
                          />
                        </div>
                      </li>
                    ))}
                  </ul>
                </SectionCard>

                <SectionCard
                  title={data.activity_section_title}
                  actionHref={data.access_history_href}
                  actionLabel={data.access_history_label}
                >
                  {data.recent_activity.length ? (
                    <ul className="space-y-4">
                      {data.recent_activity.map((item) => (
                        <li key={item.key} className="flex gap-3">
                          <span
                            className={cn(
                              "mt-1.5 size-2 shrink-0 rounded-full",
                              item.tone === "success" && "bg-[#10b981]",
                              item.tone === "error" && "bg-[#ef4444]",
                              item.tone === "info" && "bg-[#6366f1]",
                            )}
                          />
                          <div>
                            <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
                            <p className="text-[12px] text-[#6b7280]">{item.subtitle}</p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">No recent activity recorded for this account.</p>
                  )}
                </SectionCard>
              </div>
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}