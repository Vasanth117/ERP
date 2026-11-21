"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo } from "react";
import { useFieldArray, useForm } from "react-hook-form";

import { BookOpenIcon } from "@/components/icons/erp/generated/book-open";
import { GlobeIcon } from "@/components/icons/erp/generated/globe";
import { IdCardIcon } from "@/components/icons/erp/generated/id-card";
import { ReceiptIcon } from "@/components/icons/erp/generated/receipt";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useCampusContactPage,
  useSaveCampusContactPage,
} from "@/features/college-admin/hooks/use-institution";
import type {
  CampusContactPage,
  InstitutionAddress,
  InstitutionFieldMeta,
} from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

const USAGE_ICONS = [GlobeIcon, ReceiptIcon, BookOpenIcon, IdCardIcon];

type FormValues = {
  address: InstitutionAddress;
  official_contacts: {
    contact_id?: string | null;
    role_label: string;
    name: string;
    phone: string;
    email: string;
  }[];
  emergency_contacts: { contact_id?: string | null; label: string; phone: string }[];
};

function metaFor(meta: InstitutionFieldMeta[], key: string) {
  return meta.find((row) => row.key === key);
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{title}</h3>
      {children}
    </section>
  );
}

function CampusTabs({ page }: { page: CampusContactPage }) {
  return (
    <div className="flex flex-wrap gap-2 border-b border-[#e8ecf2] pb-4">
      {page.campus_tabs.map((tab) => (
        <Link
          key={tab.campus_id}
          href={tab.href}
          className={cn(
            "rounded-full px-4 py-1.5 text-[13px] font-medium",
            tab.is_active
              ? "bg-[#245dd8] text-white"
              : "border border-[#dce3ec] bg-white text-[#374151] hover:border-[#245dd8]",
          )}
        >
          {tab.name}
        </Link>
      ))}
    </div>
  );
}

export function CampusContactForm({ campusId }: { campusId: string }) {
  const router = useRouter();
  const { data, isLoading, isError, error, refetch } = useCampusContactPage(campusId);
  const save = useSaveCampusContactPage(campusId);

  const defaults = useMemo<FormValues | undefined>(() => {
    if (!data) return undefined;
    return {
      address: { ...data.address },
      official_contacts: data.official_contacts.map((row) => ({
        contact_id: row.contact_id,
        role_label: row.role_label,
        name: row.name,
        phone: row.phone ?? "",
        email: row.email ?? "",
      })),
      emergency_contacts: data.emergency_contacts.map((row) => ({
        contact_id: row.contact_id,
        label: row.label,
        phone: row.phone,
      })),
    };
  }, [data]);

  const form = useForm<FormValues>({ defaultValues: defaults });
  const officials = useFieldArray({ control: form.control, name: "official_contacts" });
  const emergencies = useFieldArray({ control: form.control, name: "emergency_contacts" });

  useEffect(() => {
    if (defaults) form.reset(defaults);
  }, [defaults, form]);

  return (
    <div className="space-y-5" data-figma-frame="72:7995">
      <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
        {data?.page_title ?? "Campus address & contact"}
      </h2>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <CampusTabs page={data} />

            <form
              className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_340px]"
              onSubmit={form.handleSubmit((values) => {
                save.mutate({
                  address: {
                    ...values.address,
                    latitude:
                      values.address.latitude != null &&
                      String(values.address.latitude).trim() !== ""
                        ? Number(values.address.latitude)
                        : null,
                    longitude:
                      values.address.longitude != null &&
                      String(values.address.longitude).trim() !== ""
                        ? Number(values.address.longitude)
                        : null,
                  },
                  official_contacts: values.official_contacts.map((row) => ({
                    contact_id: row.contact_id,
                    role_label: row.role_label,
                    name: row.name,
                    phone: row.phone || null,
                    email: row.email || null,
                  })),
                  emergency_contacts: values.emergency_contacts,
                });
              })}
            >
              <div className="space-y-5">
                <Section title="Postal address">
                  <div className="grid gap-4 sm:grid-cols-2">
                    {(["line1", "line2", "city", "postal_code", "latitude", "longitude"] as const).map(
                      (key) => {
                        const meta = metaFor(data.address_field_meta, key);
                        if (!meta) return null;
                        return (
                          <div
                            key={key}
                            className={cn(key === "line1" || key === "line2" ? "sm:col-span-2" : "")}
                          >
                            <Label className="text-[13px] text-[#374151]">
                              {meta.label}
                              {meta.required ? <span className="text-[#dc2626]"> *</span> : null}
                            </Label>
                            <Input className="mt-1.5 h-9" {...form.register(`address.${key}`)} />
                          </div>
                        );
                      },
                    )}
                    <div>
                      <Label className="text-[13px] text-[#374151]">
                        {metaFor(data.address_field_meta, "district")?.label ?? "District"}
                        <span className="text-[#dc2626]"> *</span>
                      </Label>
                      <select
                        className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                        {...form.register("address.district")}
                      >
                        {data.district_options.map((opt) => (
                          <option key={opt.value || opt.label} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <Label className="text-[13px] text-[#374151]">
                        {metaFor(data.address_field_meta, "state")?.label ?? "State"}
                        <span className="text-[#dc2626]"> *</span>
                      </Label>
                      <select
                        className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                        {...form.register("address.state")}
                      >
                        {data.state_options.map((opt) => (
                          <option key={opt.value || opt.label} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </Section>

                <Section title="Official contacts">
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[32rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] uppercase tracking-wide text-[#9ca3af]">
                          <th className="pb-2 pr-2">Contact</th>
                          <th className="pb-2 pr-2">Name</th>
                          <th className="pb-2 pr-2">Phone</th>
                          <th className="pb-2">Email</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {officials.fields.map((field, index) => (
                          <tr key={field.id}>
                            <td className="py-2 pr-2">
                              <Input
                                className="h-8"
                                {...form.register(`official_contacts.${index}.role_label`)}
                              />
                            </td>
                            <td className="py-2 pr-2">
                              <Input className="h-8" {...form.register(`official_contacts.${index}.name`)} />
                            </td>
                            <td className="py-2 pr-2">
                              <Input className="h-8" {...form.register(`official_contacts.${index}.phone`)} />
                            </td>
                            <td className="py-2">
                              <Input className="h-8" {...form.register(`official_contacts.${index}.email`)} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="mt-3 flex items-center justify-between text-[12px] text-[#6b7280]">
                    <span>{data.contact_count_label}</span>
                    {data.add_contact_enabled ? (
                      <button
                        type="button"
                        className="font-medium text-[#245dd8]"
                        onClick={() =>
                          officials.append({
                            role_label: "",
                            name: "",
                            phone: "",
                            email: "",
                          })
                        }
                      >
                        Add contact →
                      </button>
                    ) : null}
                  </div>
                </Section>
              </div>

              <div className="space-y-5">
                <Section title="Shown on">
                  <ul className="space-y-3">
                    {data.usage_contexts.map((ctx, index) => {
                      const Icon = USAGE_ICONS[index % USAGE_ICONS.length];
                      return (
                        <li key={ctx.title} className="flex gap-3">
                          <Icon className="mt-0.5 size-4 text-[#9ca3af]" aria-hidden />
                          <div>
                            <p className="text-[13px] font-medium text-[#111827]">{ctx.title}</p>
                            <p className="text-[12px] text-[#6b7280]">{ctx.description}</p>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </Section>

                <Section title="Emergency contacts">
                  <ul className="divide-y divide-[#f1f5f9]">
                    {emergencies.fields.map((field, index) => (
                      <li key={field.id} className="grid gap-2 py-3 first:pt-0">
                        <Input
                          placeholder="Label"
                          className="h-8"
                          {...form.register(`emergency_contacts.${index}.label`)}
                        />
                        <Input
                          placeholder="Phone"
                          className="h-8"
                          {...form.register(`emergency_contacts.${index}.phone`)}
                        />
                      </li>
                    ))}
                  </ul>
                  <button
                    type="button"
                    className="mt-2 text-[12px] font-medium text-[#245dd8]"
                    onClick={() => emergencies.append({ label: "", phone: "" })}
                  >
                    Add emergency line →
                  </button>
                </Section>
              </div>

              <div className="col-span-full flex flex-col gap-3 border-t border-[#e8ecf2] pt-4 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-[12px] text-[#6b7280]">{data.footer_note}</p>
                <div className="flex gap-2">
                  <Button type="button" variant="outline" onClick={() => router.push(data.cancel_href)}>
                    Cancel
                  </Button>
                  <Button type="submit" className="bg-[#245dd8] hover:bg-[#1f4fb8]" disabled={save.isPending}>
                    {save.isPending ? "Saving…" : "Save changes"}
                  </Button>
                </div>
              </div>
            </form>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}