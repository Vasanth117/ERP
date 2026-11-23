"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { UserRoundIcon } from "@/components/icons/erp/generated/user-round";
import { XIcon } from "@/components/icons/erp/generated/x";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useCreateEditRolePage,
  useSaveCreateEditRole,
} from "@/features/college-admin/hooks/use-create-edit-role";
import type {
  CreateEditRoleFormValues,
  CreateEditRolePermissionGroup,
  CreateEditRolePermissionToggle,
} from "@/features/college-admin/types/create-edit-role";
import type { InstitutionFieldMeta } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function metaFor(fieldMeta: InstitutionFieldMeta[], key: string) {
  return fieldMeta.find((row) => row.key === key);
}

function FormField({ meta, children }: { meta?: InstitutionFieldMeta; children: React.ReactNode }) {
  if (!meta) return null;
  return (
    <div className="space-y-1.5" data-field-key={meta.key}>
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

function TypeBadge({ label, tone }: { label: string; tone: string }) {
  const styles =
    tone === "info"
      ? "bg-[#eff6ff] text-[#1d4ed8]"
      : "bg-[#f3f4f6] text-[#6b7280]";
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles)}>
      <span className="size-1.5 rounded-full bg-current opacity-70" />
      {label}
    </span>
  );
}

function clonePermissionGroups(groups: CreateEditRolePermissionGroup[]): CreateEditRolePermissionGroup[] {
  return groups.map((group) => ({
    ...group,
    rows: group.rows.map((row) => ({
      ...row,
      cells: row.cells.map((cell) => ({ ...cell })),
    })),
  }));
}

function groupsToToggles(groups: CreateEditRolePermissionGroup[]): CreateEditRolePermissionToggle[] {
  const toggles: CreateEditRolePermissionToggle[] = [];
  for (const group of groups) {
    for (const row of group.rows) {
      for (const cell of row.cells) {
        if (!cell.applicable) continue;
        toggles.push({
          row_key: row.row_key,
          column_key: cell.column_key,
          checked: cell.checked,
        });
      }
    }
  }
  return toggles;
}

export function CreateEditRoleDashboard() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const roleId = useMemo(
    () => searchParams.get("roleId") ?? searchParams.get("role_id") ?? null,
    [searchParams],
  );

  const pageQuery = useCreateEditRolePage(roleId);
  const saveMutation = useSaveCreateEditRole(roleId);

  const [permissionGroups, setPermissionGroups] = useState<CreateEditRolePermissionGroup[]>([]);
  const [accessState, setAccessState] = useState({
    require_mfa: false,
    restrict_campus_network: false,
    time_bound_access: false,
  });

  const form = useForm<CreateEditRoleFormValues>({
    values: pageQuery.data?.form,
  });

  useEffect(() => {
    if (!pageQuery.data) return;
    setPermissionGroups(clonePermissionGroups(pageQuery.data.permission_groups));
    setAccessState({
      require_mfa: pageQuery.data.form.require_mfa,
      restrict_campus_network: pageQuery.data.form.restrict_campus_network,
      time_bound_access: pageQuery.data.form.time_bound_access,
    });
  }, [pageQuery.data]);

  const data = pageQuery.data;

  const toggleCell = useCallback((rowKey: string, columnKey: string, checked: boolean) => {
    setPermissionGroups((prev) =>
      prev.map((group) => ({
        ...group,
        rows: group.rows.map((row) => {
          if (row.row_key !== rowKey) return row;
          return {
            ...row,
            cells: row.cells.map((cell) =>
              cell.column_key === columnKey && cell.applicable ? { ...cell, checked } : cell,
            ),
          };
        }),
      })),
    );
  }, []);

  const submitSave = form.handleSubmit((values) => {
    if (!data?.can_save) {
      toast.error("This role cannot be modified");
      return;
    }
    const formPayload: CreateEditRoleFormValues = {
      ...values,
      require_mfa: accessState.require_mfa,
      restrict_campus_network: accessState.restrict_campus_network,
      time_bound_access: accessState.time_bound_access,
    };
    saveMutation.mutate(
      {
        form: formPayload,
        permission_toggles: groupsToToggles(permissionGroups),
      },
      {
        onSuccess: (saved) => {
          toast.success("Role saved");
          if (!roleId && saved.role_id) {
            router.replace(`/college-admin/users/create-edit-role?roleId=${saved.role_id}`);
            return;
          }
          router.push(data?.back_href ?? "/college-admin/users/role-management-dashboard");
        },
        onError: onCollegeAdminMutationError,
      },
    );
  });

  const resetForm = useCallback(() => {
    if (data) {
      form.reset(data.form);
      setPermissionGroups(clonePermissionGroups(data.permission_groups));
      setAccessState({
        require_mfa: data.form.require_mfa,
        restrict_campus_network: data.form.restrict_campus_network,
        time_bound_access: data.form.time_bound_access,
      });
    }
  }, [data, form]);

  const isBusy = saveMutation.isPending;
  const fieldMeta = data?.role_details_field_meta ?? [];

  return (
    <div className="space-y-5" data-figma-frame="69:126595">
      <PageHeader data={data} isBusy={isBusy} onCancel={resetForm} onSave={() => void submitSave()} />

      <QueryState query={pageQuery}>
        {data ? (
          <div className="grid gap-5 lg:grid-cols-3">
            <div className="space-y-5 lg:col-span-2">
              <Section title={data.role_details_section_title}>
                <div className="grid gap-4 sm:grid-cols-2">
                  <FormField meta={metaFor(fieldMeta, "name")}>
                    <Input
                      {...form.register("name")}
                      disabled={!data.can_save || isBusy}
                      className="h-9 text-[13px]"
                    />
                  </FormField>
                  <FormField meta={metaFor(fieldMeta, "role_code")}>
                    <Input
                      {...form.register("role_code")}
                      disabled={!data.can_save || isBusy}
                      className="h-9 text-[13px] uppercase"
                    />
                  </FormField>
                  <FormField meta={metaFor(fieldMeta, "base_role")}>
                    <select
                      {...form.register("base_role")}
                      disabled={!data.can_save || isBusy}
                      className="h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#111827]"
                    >
                      {data.base_role_options.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </FormField>
                  <FormField meta={metaFor(fieldMeta, "scope")}>
                    <select
                      {...form.register("scope")}
                      disabled={!data.can_save || isBusy}
                      className="h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#111827]"
                    >
                      {data.scope_options.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </FormField>
                </div>
                <DescriptionField
                  fieldMeta={fieldMeta}
                  disabled={!data.can_save || isBusy}
                  register={form.register}
                />
              </Section>

              <Section title={data.module_permissions_section_title}>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[640px] border-collapse text-[12px]">
                    <thead>
                      <tr className="border-b border-[#e8ecf2] text-left text-[11px] font-semibold uppercase tracking-wide text-[#6b7280]">
                        {data.permission_columns.map((col, idx) => (
                          <th
                            key={col}
                            className={cn(
                              "pb-2 pr-2",
                              idx === 0 ? "w-[40%] pl-0" : "w-[12%] text-center",
                            )}
                          >
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {permissionGroups.map((group) => (
                        <Fragment key={group.group_key}>
                          <tr>
                            <td
                              colSpan={data.permission_columns.length}
                              className="pb-1 pt-4 text-[13px] font-semibold text-[#111827]"
                            >
                              {group.group_label}
                            </td>
                          </tr>
                          {group.rows.map((row) => (
                            <tr key={row.row_key} className="border-b border-[#f1f5f9]">
                              <td className="py-2.5 pr-2 text-[13px] text-[#374151]">{row.label}</td>
                              {row.cells.map((cell) => (
                                <td key={cell.column_key} className="py-2.5 text-center">
                                  {!cell.applicable ? (
                                    <span className="text-[#9ca3af]">—</span>
                                  ) : (
                                    <input
                                      type="checkbox"
                                      className="size-4 rounded border-[#cbd5e1] text-[#245dd8] focus:ring-[#245dd8]/30"
                                      checked={cell.checked}
                                      disabled={!data.can_save || isBusy}
                                      onChange={(e) => toggleCell(row.row_key, cell.column_key, e.target.checked)}
                                    />
                                  )}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </Fragment>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Section>
            </div>

            <RoleSidebar
              data={data}
              accessState={accessState}
              setAccessState={setAccessState}
              disabled={!data.can_save || isBusy}
            />
          </div>
        ) : null}
      </QueryState>

      {data ? (
        <footer className="sticky bottom-0 z-10 -mx-1 flex flex-col gap-3 border-t border-[#e8ecf2] bg-[#f5f7fa]/95 px-1 py-4 backdrop-blur sm:flex-row sm:items-center sm:justify-between">
          <p className="text-[12px] text-[#6b7280]">{data.footer_note}</p>
          <div className="flex gap-2">
            <Link
              href={data.cancel_href}
              className="inline-flex h-9 items-center rounded-md px-4 text-xs font-medium text-[#374151] hover:bg-white"
            >
              {data.cancel_label}
            </Link>
            <button
              type="button"
              disabled={!data.can_save || isBusy}
              onClick={() => void submitSave()}
              className="inline-flex h-9 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1d4ed8] disabled:opacity-50"
            >
              {data.save_label}
            </button>
          </div>
        </footer>
      ) : null}
    </div>
  );
}

function DescriptionField({
  fieldMeta,
  disabled,
  register,
}: {
  fieldMeta: InstitutionFieldMeta[];
  disabled: boolean;
  register: ReturnType<typeof useForm<CreateEditRoleFormValues>>["register"];
}) {
  const meta = metaFor(fieldMeta, "description");
  if (!meta) return null;
  return (
    <div className="mt-4">
      <FormField meta={meta}>
        <textarea
          {...register("description")}
          disabled={disabled}
          rows={3}
          className="w-full rounded-md border border-[#dce3ec] bg-white px-3 py-2 text-[13px] text-[#111827]"
        />
      </FormField>
    </div>
  );
}

function PageHeader({
  data,
  isBusy,
  onCancel,
  onSave,
}: {
  data?: import("@/features/college-admin/types/create-edit-role").CreateEditRolePage;
  isBusy: boolean;
  onCancel: () => void;
  onSave: () => void;
}) {
  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div className="flex min-w-0 items-start gap-3">
        <Link
          href={data?.back_href ?? "/college-admin/users/role-management-dashboard"}
          className="mt-1 inline-flex size-8 items-center justify-center rounded-md border border-[#e5e7eb] bg-white text-[#374151] hover:bg-[#f9fafb]"
          aria-label="Back"
        >
          <ChevronLeftIcon className="size-4" />
        </Link>
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
              {data?.page_title ?? "Create / Edit Role"}
            </h2>
            {data ? <TypeBadge label={data.type_badge_label} tone={data.type_badge_tone} /> : null}
          </div>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
      </div>
      <div className="flex shrink-0 flex-wrap gap-2">
        <button
          type="button"
          disabled={!data || isBusy}
          onClick={onCancel}
          className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
        >
          <XIcon className="size-3.5" aria-hidden />
          {data?.cancel_label ?? "Cancel"}
        </button>
        <button
          type="button"
          disabled={!data?.can_save || isBusy}
          onClick={onSave}
          className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1d4ed8] disabled:opacity-50"
        >
          <CheckIcon className="size-3.5" aria-hidden />
          {data?.save_label ?? "Save role"}
        </button>
      </div>
    </div>
  );
}

function RoleSidebar({
  data,
  accessState,
  setAccessState,
  disabled,
}: {
  data: import("@/features/college-admin/types/create-edit-role").CreateEditRolePage;
  accessState: {
    require_mfa: boolean;
    restrict_campus_network: boolean;
    time_bound_access: boolean;
  };
  setAccessState: React.Dispatch<
    React.SetStateAction<{
      require_mfa: boolean;
      restrict_campus_network: boolean;
      time_bound_access: boolean;
    }>
  >;
  disabled: boolean;
}) {
  return (
    <div className="space-y-5">
      <Section title={data.access_rules_section_title}>
        <ul className="space-y-4">
          {data.access_toggles.map((toggle) => {
            const key = toggle.key as keyof typeof accessState;
            const checked = accessState[key];
            return (
              <li key={toggle.key} className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-[13px] font-medium text-[#111827]">{toggle.label}</p>
                  <p className="text-[11px] text-[#6b7280]">{toggle.description}</p>
                </div>
                <label className="relative inline-flex cursor-pointer items-center">
                  <input
                    type="checkbox"
                    className="peer sr-only"
                    checked={checked}
                    disabled={disabled}
                    onChange={(e) =>
                      setAccessState((prev) => ({
                        ...prev,
                        [key]: e.target.checked,
                      }))
                    }
                  />
                  <span className="h-5 w-9 rounded-full bg-[#e5e7eb] after:absolute after:left-0.5 after:top-0.5 after:size-4 after:rounded-full after:bg-white after:transition peer-checked:bg-[#245dd8] peer-checked:after:translate-x-4" />
                </label>
              </li>
            );
          })}
        </ul>
      </Section>

      <Section title={data.users_with_role_section_title}>
        <div className="mb-3 flex items-center justify-between">
          <span className="text-[12px] text-[#6b7280]">
            {data.is_create ? "No users yet" : `${data.assigned_users.length} shown`}
          </span>
          <Link href={data.assign_users_href} className="text-[12px] font-medium text-[#245dd8] hover:underline">
            {data.assign_users_label} →
          </Link>
        </div>
        <ul className="space-y-3">
          {data.assigned_users.map((user) => (
            <li key={user.user_id}>
              <Link
                href={user.detail_href}
                className="flex items-center gap-3 rounded-lg border border-transparent px-1 py-1 hover:border-[#e8ecf2] hover:bg-[#f9fafb]"
              >
                <span className="flex size-9 items-center justify-center rounded-full bg-[#f3f4f6] text-[#6b7280]">
                  <UserRoundIcon className="size-4" />
                </span>
                <span>
                  <span className="block text-[13px] font-medium text-[#111827]">{user.name}</span>
                  <span className="block text-[11px] text-[#6b7280]">{user.subtitle}</span>
                </span>
              </Link>
            </li>
          ))}
          {data.more_users_label ? (
            <li className="flex items-center gap-3 px-1 py-1 text-[13px] text-[#6b7280]">
              <span className="flex size-9 items-center justify-center rounded-full bg-[#f3f4f6]">
                <UserRoundIcon className="size-4" />
              </span>
              {data.more_users_label}
            </li>
          ) : null}
        </ul>
      </Section>
    </div>
  );
}