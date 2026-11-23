"use client";

import Link from "next/link";
import { useCallback, useMemo, useRef, useState, type ChangeEvent, type ReactNode } from "react";
import { useForm } from "react-hook-form";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { EyeIcon } from "@/components/icons/erp/generated/eye";
import { MonitorPlayIcon } from "@/components/icons/erp/generated/monitor-play";
import { PencilIcon } from "@/components/icons/erp/generated/pencil";
import { ReceiptIcon } from "@/components/icons/erp/generated/receipt";
import { UploadIcon } from "@/components/icons/erp/generated/upload";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { InstitutionIdentityMark } from "@/features/college-admin/components/institution/institution-identity-mark";
import {
  BrandingAssetPreviewDialog,
  BrandingPortalPreviewDialog,
  type BrandingAssetPreviewTarget,
} from "@/features/college-admin/components/institution/institution-branding-preview-dialog";
import {
  InstitutionPageActionFooter,
  institutionActionButtonOutline,
  institutionActionButtonPrimary,
} from "@/features/college-admin/components/institution/institution-page-action-footer";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useInstitutionBrandingPage,
  usePublishInstitutionBranding,
  useSaveInstitutionBrandingDraft,
  useUploadBrandingAsset,
} from "@/features/college-admin/hooks/use-institution";
import type {
  BrandingAssetRow,
  BrandingDocumentTemplateRow,
  InstitutionBrandingFormValues,
  InstitutionBrandingPage,
} from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function Section({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="border-b border-[#f1f5f9] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
        {subtitle ? <p className="mt-0.5 text-[12px] text-[#9ca3af]">{subtitle}</p> : null}
      </div>
      <div className="px-5 py-4">{children}</div>
    </section>
  );
}

function StatusPill({ label, tone }: { label: string; tone: "success" | "warning" | "muted" }) {
  const styles = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  return (
    <span className={cn("rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[tone])}>{label}</span>
  );
}

function templateTone(status: string): "success" | "warning" | "muted" {
  if (status === "published") return "success";
  if (status === "draft") return "warning";
  return "muted";
}

function buildDefaults(page: InstitutionBrandingPage): InstitutionBrandingFormValues {
  return { ...page.form };
}

function toPayload(values: InstitutionBrandingFormValues): Record<string, unknown> {
  return { ...values };
}

function ColorInput({
  label,
  required,
  value,
  onChange,
}: {
  label: string;
  required?: boolean;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-[13px] font-medium text-[#374151]">
        {label}
        {required ? <span className="text-[#dc2626]"> *</span> : null}
      </label>
      <div className="flex items-center gap-2">
        <span
          className="size-8 shrink-0 rounded border border-[#e5e7eb]"
          style={{ backgroundColor: value || "#ffffff" }}
        />
        <Input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="border-[#dce3ec] font-mono text-[13px]"
        />
      </div>
    </div>
  );
}

function AssetRow({
  row,
  onEdit,
  onPreview,
}: {
  row: BrandingAssetRow;
  onEdit?: () => void;
  onPreview?: () => void;
}) {
  const tone = row.status === "uploaded" ? "success" : "warning";
  return (
    <li className="flex items-start justify-between gap-3 border-b border-[#f1f5f9] py-3 last:border-0">
      <div className="min-w-0">
        <p className="text-[13px] font-medium text-[#111827]">{row.label}</p>
        <p className="text-[12px] text-[#6b7280]">{row.detail_line}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <StatusPill label={row.status_label} tone={tone} />
        {row.file_id && onPreview ? (
          <button
            type="button"
            onClick={onPreview}
            className="text-[#9ca3af] hover:text-[#245dd8]"
            aria-label={`Preview ${row.label}`}
          >
            <EyeIcon className="size-3.5" />
          </button>
        ) : null}
        {row.editable && onEdit ? (
          <button
            type="button"
            onClick={onEdit}
            className="text-[#9ca3af] hover:text-[#245dd8]"
            aria-label={`Upload ${row.label}`}
          >
            <PencilIcon className="size-3.5" />
          </button>
        ) : null}
      </div>
    </li>
  );
}

export function InstitutionBrandingForm() {
  const pageQuery = useInstitutionBrandingPage();
  const saveDraft = useSaveInstitutionBrandingDraft();
  const publish = usePublishInstitutionBranding();
  const uploadAsset = useUploadBrandingAsset();
  const primaryInputRef = useRef<HTMLInputElement>(null);
  const assetInputRef = useRef<HTMLInputElement>(null);
  const pendingAssetKey = useRef<string>("primary_logo");
  const [portalPreviewOpen, setPortalPreviewOpen] = useState(false);
  const [assetPreview, setAssetPreview] = useState<BrandingAssetPreviewTarget | null>(null);

  const openAssetPreview = useCallback((row: BrandingAssetRow) => {
    if (!row.file_id) return;
    setAssetPreview({
      fileId: row.file_id,
      label: row.label,
      detailLine: row.detail_line,
    });
  }, []);

  const defaults = useMemo(
    () => (pageQuery.data ? buildDefaults(pageQuery.data) : undefined),
    [pageQuery.data],
  );

  const form = useForm<InstitutionBrandingFormValues>({ values: defaults });
  const watchedForm = form.watch();
  const data = pageQuery.data;
  const isBusy = saveDraft.isPending || publish.isPending || uploadAsset.isPending;

  const discard = useCallback(() => {
    if (data) form.reset(buildDefaults(data));
  }, [data, form]);

  const submitPublish = form.handleSubmit((values) => publish.mutate(toPayload(values)));
  const handleSaveDraft = form.handleSubmit((values) => saveDraft.mutate(toPayload(values)));

  const uploadFile = useCallback(
    (assetKey: string, file: File, label: string) => {
      uploadAsset.mutate(
        { assetKey, file },
        {
          onSuccess: (result) => {
            void pageQuery.refetch().then(() => {
              if (result.file_id) {
                setAssetPreview({
                  fileId: result.file_id,
                  label,
                  detailLine: result.file_name ?? file.name,
                });
              }
            });
          },
        },
      );
    },
    [pageQuery, uploadAsset],
  );

  const onPrimaryFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) uploadFile("primary_logo", file, "Primary logo");
    event.target.value = "";
  };

  const onAssetFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const row = data?.brand_assets.find((r) => r.asset_key === pendingAssetKey.current);
      uploadFile(pendingAssetKey.current, file, row?.label ?? "Brand asset");
    }
    event.target.value = "";
  };

  const previewPrimaryLogo = useCallback(() => {
    if (!data?.primary_logo.file_id) return;
    setAssetPreview({
      fileId: data.primary_logo.file_id,
      label: "Primary logo",
      detailLine: data.primary_logo.current_summary ?? undefined,
    });
  }, [data]);

  const colorValue = (key: keyof InstitutionBrandingFormValues) =>
    String(form.watch(key) ?? "");

  return (
    <div className="space-y-5" data-figma-frame="72:6775">
      <div className="min-w-0">
        <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
          College Logo &amp; Branding
        </h2>
        <p className="mt-1 text-[14px] text-[#6b7280]">
          Logos, colours and templates used across portals, documents and ID cards.
        </p>
      </div>

      <input ref={primaryInputRef} type="file" className="hidden" accept="image/*,.svg" onChange={onPrimaryFile} />
      <input ref={assetInputRef} type="file" className="hidden" accept="image/*,.svg,.ico" onChange={onAssetFile} />

      <QueryState
        isLoading={pageQuery.isLoading}
        isError={pageQuery.isError}
        error={pageQuery.error}
        onRetry={() => void pageQuery.refetch()}
      >
        {data ? (
          <>
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_392px]">
              <div className="space-y-5">
                <Section title="Primary logo" subtitle={data.primary_logo.upload_hint}>
                  <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-[#cbd5e1] bg-[#f8fafc] px-6 py-10 text-center">
                    {data.primary_logo.file_id ? (
                      <button
                        type="button"
                        onClick={previewPrimaryLogo}
                        className="mb-4 rounded-xl outline-offset-2 transition hover:opacity-95 focus-visible:outline-2 focus-visible:outline-[#245dd8]"
                        aria-label="Preview primary logo"
                      >
                        <InstitutionIdentityMark
                          displayName={String(data.form.display_name ?? "College")}
                          logoFileId={data.primary_logo.file_id}
                          accent={colorValue("primary_color") || "#245dd8"}
                          size="lg"
                          className="shadow-md"
                        />
                      </button>
                    ) : (
                      <UploadIcon className="size-8 text-[#94a3b8]" aria-hidden />
                    )}
                    <p className="mt-3 text-[13px] font-medium text-[#374151]">
                      {data.primary_logo.file_id
                        ? "College logo on file"
                        : "Drop the college logo here"}
                    </p>
                    {data.primary_logo.current_summary ? (
                      <p className="mt-1 text-[12px] text-[#6b7280]">{data.primary_logo.current_summary}</p>
                    ) : (
                      <p className="mt-1 text-[12px] text-[#9ca3af]">No logo uploaded yet</p>
                    )}
                    <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
                      {data.primary_logo.file_id ? (
                        <Button
                          type="button"
                          variant="outline"
                          className="h-9 gap-1.5 border-[#dce3ec] text-xs"
                          onClick={previewPrimaryLogo}
                          disabled={isBusy}
                        >
                          <EyeIcon className="size-3.5" aria-hidden />
                          Preview
                        </Button>
                      ) : null}
                      <Button
                        type="button"
                        variant="outline"
                        className="h-9 border-[#dce3ec] text-xs"
                        onClick={() => primaryInputRef.current?.click()}
                        disabled={isBusy}
                      >
                        {data.primary_logo.file_id ? "Replace logo" : "Browse files"}
                      </Button>
                    </div>
                  </div>
                </Section>

                <Section title="Brand colours">
                  <div className="grid gap-4 sm:grid-cols-2">
                    {data.color_fields.map((field) => (
                      <ColorInput
                        key={field.key}
                        label={field.label}
                        required={field.required}
                        value={colorValue(field.key as keyof InstitutionBrandingFormValues)}
                        onChange={(v) =>
                          form.setValue(field.key as keyof InstitutionBrandingFormValues, v)
                        }
                      />
                    ))}
                  </div>
                </Section>

                <Section title="Document templates">
                  <TemplateTable rows={data.document_templates} />
                  <div className="mt-3 flex items-center justify-between border-t border-[#f1f5f9] pt-3 text-[12px]">
                    <span className="text-[#6b7280]">{data.template_count_label}</span>
                    <Link
                      href={data.templates_manage_href}
                      className="font-medium text-[#245dd8] hover:underline"
                    >
                      Manage templates →
                    </Link>
                  </div>
                </Section>
              </div>

              <div className="space-y-5">
                <Section title="Brand assets">
                  <ul>
                    {data.brand_assets.map((row) => (
                      <AssetRow
                        key={row.asset_key}
                        row={row}
                        onPreview={() => openAssetPreview(row)}
                        onEdit={() => {
                          pendingAssetKey.current = row.asset_key;
                          assetInputRef.current?.click();
                        }}
                      />
                    ))}
                  </ul>
                </Section>

                <Section title="Preview">
                  <ul className="divide-y divide-[#f1f5f9]">
                    {data.preview_items.map((item, index) => {
                      const Icon = index === 0 ? MonitorPlayIcon : ReceiptIcon;
                      return (
                        <li key={item.title} className="flex gap-3 py-3 first:pt-0">
                          <Icon className="mt-0.5 size-[18px] shrink-0 text-[#9ca3af]" aria-hidden />
                          <div>
                            <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
                            <p className="text-[12px] text-[#6b7280]">{item.description}</p>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                  <Button
                    type="button"
                    variant="outline"
                    className="mt-4 h-9 w-full gap-1.5 border-[#dce3ec] text-xs"
                    onClick={() => setPortalPreviewOpen(true)}
                  >
                    <EyeIcon className="size-3.5" aria-hidden />
                    Open full preview
                  </Button>
                </Section>
              </div>
            </div>

            <BrandingPortalPreviewDialog
              open={portalPreviewOpen}
              data={data}
              formValues={watchedForm}
              onClose={() => setPortalPreviewOpen(false)}
            />
            <BrandingAssetPreviewDialog
              open={Boolean(assetPreview)}
              target={assetPreview}
              onClose={() => setAssetPreview(null)}
            />

            <InstitutionPageActionFooter note={data.footer_note}>
              <Button
                type="button"
                variant="outline"
                className={cn(
                  institutionActionButtonOutline,
                  "gap-1.5 hover:bg-[#f9fafb]",
                )}
                onClick={() => setPortalPreviewOpen(true)}
                disabled={isBusy}
              >
                <EyeIcon className="size-3.5" aria-hidden />
                Preview portal
              </Button>
              <Button
                type="button"
                variant="outline"
                className={institutionActionButtonOutline}
                onClick={discard}
                disabled={isBusy}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="outline"
                className={institutionActionButtonOutline}
                onClick={() => void handleSaveDraft()}
                disabled={isBusy}
              >
                Save draft
              </Button>
              <Button
                type="button"
                className={institutionActionButtonPrimary}
                onClick={() => void submitPublish()}
                disabled={isBusy}
              >
                <CheckIcon className="size-3.5" aria-hidden />
                Publish branding
              </Button>
            </InstitutionPageActionFooter>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}

function TemplateTable({ rows }: { rows: BrandingDocumentTemplateRow[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[520px] text-left text-[13px]">
        <thead>
          <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
            <th className="pb-2 pr-4 font-medium">Template</th>
            <th className="pb-2 pr-4 font-medium">Used for</th>
            <th className="pb-2 pr-4 font-medium">Last updated</th>
            <th className="pb-2 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.template_key} className="border-b border-[#f1f5f9] last:border-0">
              <td className="py-3 pr-4 font-medium text-[#111827]">{row.title}</td>
              <td className="py-3 pr-4 text-[#6b7280]">{row.used_for}</td>
              <td className="py-3 pr-4 text-[#6b7280]">{row.last_updated_label}</td>
              <td className="py-3">
                <StatusPill label={row.status_label} tone={templateTone(row.status)} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}