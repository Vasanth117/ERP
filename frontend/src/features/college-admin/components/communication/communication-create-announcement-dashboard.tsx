"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";

import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { FileTextIcon } from "@/components/icons/erp/generated/file-text";
import { SendIcon } from "@/components/icons/erp/generated/send";
import { XIcon } from "@/components/icons/erp/generated/x";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  institutionActionButtonOutline,
  institutionActionButtonPrimary,
} from "@/features/college-admin/components/institution/institution-page-action-footer";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useCommunicationCreateAnnouncementPage,
  useSaveCommunicationCreateAnnouncementPage,
} from "@/features/college-admin/hooks/use-communication-create-announcement";
import type { CommunicationCreateAnnouncementFormValues } from "@/features/college-admin/types/communication-create-announcement";
import { cn } from "@/lib/utils";

function ToggleRow({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (next: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-3 border-t border-[#f1f5f9] pt-4">
      <p className="text-[13px] font-medium text-[#111827]">{label}</p>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={cn(
          "relative h-6 w-11 shrink-0 rounded-full transition-colors",
          checked ? "bg-[#245dd8]" : "bg-[#d1d5db]",
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 size-5 rounded-full bg-white shadow transition-transform",
            checked ? "left-[22px]" : "left-0.5",
          )}
        />
      </button>
    </div>
  );
}

function ChannelTags({
  selected,
  options,
  onChange,
}: {
  selected: string[];
  options: { value: string; label: string }[];
  onChange: (next: string[]) => void;
}) {
  const toggle = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value));
    } else {
      onChange([...selected, value]);
    }
  };
  return (
    <div className="flex min-h-[2.25rem] flex-wrap gap-2 rounded-md border border-[#dce3ec] bg-white px-2 py-1.5">
      {selected.map((value) => {
        const label = options.find((o) => o.value === value)?.label ?? value;
        return (
          <button
            key={value}
            type="button"
            onClick={() => toggle(value)}
            className="inline-flex items-center gap-1 rounded-md bg-[#eff6ff] px-2 py-0.5 text-[12px] font-medium text-[#1d4ed8]"
          >
            {label}
            <span aria-hidden>×</span>
          </button>
        );
      })}
      {options
        .filter((o) => o.value && !selected.includes(o.value))
        .map((o) => (
          <button
            key={o.value}
            type="button"
            onClick={() => toggle(o.value)}
            className="text-[12px] text-[#6b7280] hover:text-[#245dd8]"
          >
            + {o.label}
          </button>
        ))}
    </div>
  );
}

export function CommunicationCreateAnnouncementDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const announcementId = searchParams?.get("announcement_id") ?? undefined;
  const presetAudience = searchParams?.get("audience") ?? undefined;
  const presetChannels = searchParams?.get("preset_channels") ?? undefined;
  const presetPublishTiming = searchParams?.get("publish_timing") ?? undefined;

  const { data, isLoading, isError, error, refetch } = useCommunicationCreateAnnouncementPage(
    announcementId,
    announcementId ? undefined : presetAudience,
    announcementId ? undefined : presetChannels,
    announcementId ? undefined : presetPublishTiming,
  );
  const save = useSaveCommunicationCreateAnnouncementPage();

  const defaults = useMemo(() => data?.form, [data?.form]);
  const form = useForm<CommunicationCreateAnnouncementFormValues>({ defaultValues: defaults });

  useEffect(() => {
    if (defaults) form.reset(defaults);
  }, [defaults, form]);

  const watchChannels = form.watch("channels") ?? [];
  const watchPublish = form.watch("publish_timing");

  const submit = (action: "draft" | "publish") => {
    form.handleSubmit((values) => {
      save.mutate(
        { action, form: values },
        {
          onSuccess: (page) => {
            const id = page.form.announcement_id;
            if (id && id !== announcementId) {
              router.replace(`/college-admin/communication/create-announcement?announcement_id=${id}`);
            }
          },
        },
      );
    })();
  };

  return (
    <CollegeAdminModulePageLayout figmaFrame="161:7642">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex min-w-0 items-start gap-2">
          {data ? (
            <Link
              href={data.back_href}
              className="mt-1 inline-flex size-8 items-center justify-center rounded-md border border-[#dce3ec] text-[#374151] hover:bg-[#f9fafb]"
              aria-label={data.back_label}
            >
              <ChevronLeftIcon className="size-4" aria-hidden />
            </Link>
          ) : null}
          <div>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
              {data?.page_title ?? "Create Announcement"}
            </h2>
            <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "Compose, target and schedule"}</p>
          </div>
        </div>
        {data ? (
          <div className="flex shrink-0 flex-wrap items-center gap-2">
            <Link
              href={data.back_href}
              className={cn(buttonVariants({ variant: "outline" }), institutionActionButtonOutline)}
            >
              <XIcon className="mr-1.5 size-3.5" aria-hidden />
              {data.cancel_label}
            </Link>
            <Button
              type="button"
              variant="outline"
              className={institutionActionButtonOutline}
              disabled={save.isPending}
              onClick={() => submit("draft")}
            >
              <FileTextIcon className="mr-1.5 size-3.5" aria-hidden />
              {data.save_draft_label}
            </Button>
            <Button
              type="button"
              className={institutionActionButtonPrimary}
              disabled={save.isPending}
              onClick={() => submit("publish")}
            >
              <SendIcon className="size-3.5" aria-hidden />
              {data.publish_label}
            </Button>
          </div>
        ) : null}
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_320px]">
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.message_section_title}</h3>
              </div>
              <div className="space-y-4 px-5 py-4">
                <div>
                  <Label className="text-[13px] text-[#374151]">
                    Title <span className="text-[#ef4444]">*</span>
                  </Label>
                  <Input
                    className="mt-1.5 h-9 border-[#dce3ec] text-[13px]"
                    {...form.register("title", { required: true })}
                  />
                </div>
                <div>
                  <Label className="text-[13px] text-[#374151]">
                    Message <span className="text-[#ef4444]">*</span>
                  </Label>
                  <Textarea
                    className="mt-1.5 min-h-[120px] border-[#dce3ec] text-[13px]"
                    {...form.register("body", { required: true })}
                  />
                </div>
                <div>
                  <Label className="text-[13px] text-[#374151]">Attachment</Label>
                  <Input
                    className="mt-1.5 h-9 border-[#dce3ec] text-[13px]"
                    placeholder="File name"
                    {...form.register("attachment_name")}
                  />
                </div>
              </div>
            </section>

            <section className="h-fit overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.audience_section_title}</h3>
              <div className="space-y-4">
                <div>
                  <Label className="text-[13px] text-[#374151]">Audience</Label>
                  <select
                    className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
                    value={form.watch("audience")}
                    onChange={(e) => form.setValue("audience", e.target.value, { shouldDirty: true })}
                  >
                    {data.audience_options.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label className="text-[13px] text-[#374151]">Departments</Label>
                  <select
                    className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
                    value={form.watch("department_scope")}
                    onChange={(e) => form.setValue("department_scope", e.target.value, { shouldDirty: true })}
                  >
                    {data.department_options.map((opt) => (
                      <option key={opt.value || opt.label} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label className="text-[13px] text-[#374151]">Channels</Label>
                  <div className="mt-1.5">
                    <ChannelTags
                      selected={watchChannels}
                      options={data.channel_options}
                      onChange={(next) => form.setValue("channels", next, { shouldDirty: true })}
                    />
                  </div>
                </div>
                <div>
                  <Label className="text-[13px] text-[#374151]">Publish</Label>
                  <select
                    className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
                    value={watchPublish}
                    onChange={(e) => form.setValue("publish_timing", e.target.value, { shouldDirty: true })}
                  >
                    {data.publish_options.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
                {watchPublish === "schedule" ? (
                  <div>
                    <Label className="text-[13px] text-[#374151]">Scheduled for</Label>
                    <Input
                      type="datetime-local"
                      className="mt-1.5 h-9 border-[#dce3ec] text-[13px]"
                      value={form.watch("scheduled_for")?.slice(0, 16) ?? ""}
                      onChange={(e) => form.setValue("scheduled_for", e.target.value, { shouldDirty: true })}
                    />
                  </div>
                ) : null}
                <ToggleRow
                  label={data.pin_to_dashboard_label}
                  checked={Boolean(form.watch("pin_to_dashboard"))}
                  onChange={(next) => form.setValue("pin_to_dashboard", next, { shouldDirty: true })}
                />
              </div>
            </section>
          </div>
        ) : null}
      </QueryState>
    </CollegeAdminModulePageLayout>
  );
}