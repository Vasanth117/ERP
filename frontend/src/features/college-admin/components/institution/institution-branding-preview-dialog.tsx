"use client";

import { useCallback, useEffect, useId, type ReactNode } from "react";
import { createPortal } from "react-dom";

import { XIcon } from "@/components/icons/erp/generated/x";
import { useInstitutionBrandingLogoUrl } from "@/features/college-admin/hooks/use-institution-branding-logo";
import type {
  BrandingAssetRow,
  BrandingDocumentTemplateRow,
  InstitutionBrandingFormValues,
  InstitutionBrandingPage,
} from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

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

function PreviewDialogShell({
  open,
  title,
  subtitle,
  onClose,
  children,
  wide,
}: {
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}) {
  const titleId = useId();
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

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-[#0f172a]/45 p-4 backdrop-blur-[2px]"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className={cn(
          "flex max-h-[min(90vh,880px)] w-full flex-col overflow-hidden rounded-2xl border border-[#e2e8f0] bg-white shadow-[0_24px_48px_rgba(15,23,42,0.18)]",
          wide ? "max-w-4xl" : "max-w-lg",
        )}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b border-[#f1f5f9] px-6 py-4">
          <div className="min-w-0">
            <h2 id={titleId} className="text-[17px] font-semibold tracking-tight text-[#111827]">
              {title}
            </h2>
            {subtitle ? (
              <p className="mt-1 text-[13px] text-[#6b7280]">{subtitle}</p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex size-9 shrink-0 items-center justify-center rounded-lg border border-[#e5e7eb] text-[#6b7280] hover:bg-[#f9fafb] hover:text-[#111827]"
            aria-label="Close preview"
          >
            <XIcon className="size-4" aria-hidden />
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">{children}</div>
      </div>
    </div>,
    document.body,
  );
}

function BrandingImagePreview({
  fileId,
  alt,
  className,
  contain = true,
}: {
  fileId: string | null | undefined;
  alt: string;
  className?: string;
  contain?: boolean;
}) {
  const url = useInstitutionBrandingLogoUrl(fileId);
  if (!url) {
    return (
      <div
        className={cn(
          "flex items-center justify-center rounded-lg border border-dashed border-[#cbd5e1] bg-[#f8fafc] text-[12px] text-[#9ca3af]",
          className,
        )}
      >
        No image
      </div>
    );
  }
  return (
    // eslint-disable-next-line @next/next/no-img-element -- authenticated blob URL
    <img
      src={url}
      alt={alt}
      className={cn(
        contain ? "object-contain" : "object-cover",
        "rounded-lg border border-[#e8ecf2] bg-[#f8fafc]",
        className,
      )}
    />
  );
}

export type BrandingAssetPreviewTarget = {
  label: string;
  detailLine?: string;
  fileId: string;
};

export function BrandingAssetPreviewDialog({
  open,
  target,
  onClose,
}: {
  open: boolean;
  target: BrandingAssetPreviewTarget | null;
  onClose: () => void;
}) {
  return (
    <PreviewDialogShell
      open={open && Boolean(target)}
      title={target?.label ?? "Preview"}
      subtitle={target?.detailLine}
      onClose={onClose}
    >
      {target ? (
        <div className="flex flex-col items-center gap-4">
          <BrandingImagePreview
            fileId={target.fileId}
            alt={target.label}
            className="max-h-[min(60vh,520px)] w-full max-w-full"
          />
          <p className="text-center text-[12px] text-[#9ca3af]">
            This is how the file will appear when used in documents and portals.
          </p>
        </div>
      ) : null}
    </PreviewDialogShell>
  );
}

function PortalHeaderMock({
  displayName,
  primaryColor,
  textOnPrimary,
  logoFileId,
}: {
  displayName: string;
  primaryColor: string;
  textOnPrimary: string;
  logoFileId: string | null;
}) {
  const logoUrl = useInstitutionBrandingLogoUrl(logoFileId);
  return (
    <div className="overflow-hidden rounded-xl border border-[#e2e8f0] shadow-sm">
      <div
        className="flex items-center gap-3 px-4 py-3.5"
        style={{ backgroundColor: primaryColor }}
      >
        <div className="flex size-9 items-center justify-center overflow-hidden rounded-lg bg-white/15">
          {logoUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={logoUrl} alt="" className="max-h-8 max-w-8 object-contain" />
          ) : (
            <span className="text-[11px] font-bold text-white/80">LOGO</span>
          )}
        </div>
        <div className="min-w-0">
          <p className="truncate text-[13px] font-semibold" style={{ color: textOnPrimary }}>
            {displayName}
          </p>
          <p className="text-[11px] opacity-80" style={{ color: textOnPrimary }}>
            Student portal header
          </p>
        </div>
      </div>
      <div className="space-y-2 bg-[#f8fafc] px-4 py-3">
        <div className="h-2 w-3/4 rounded bg-[#e2e8f0]" />
        <div className="h-2 w-1/2 rounded bg-[#e2e8f0]" />
      </div>
    </div>
  );
}

function FeeReceiptMock({
  displayName,
  primaryColor,
  logoFileId,
  sealFileId,
}: {
  displayName: string;
  primaryColor: string;
  logoFileId: string | null;
  sealFileId: string | null;
}) {
  const logoUrl = useInstitutionBrandingLogoUrl(logoFileId);
  const sealUrl = useInstitutionBrandingLogoUrl(sealFileId);
  return (
    <div className="rounded-xl border border-[#e2e8f0] bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3 border-b border-[#f1f5f9] pb-3">
        <div className="flex items-center gap-2">
          {logoUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={logoUrl} alt="" className="size-10 object-contain" />
          ) : (
            <div className="size-10 rounded bg-[#f1f5f9]" />
          )}
          <div>
            <p className="text-[13px] font-semibold text-[#111827]">{displayName}</p>
            <p className="text-[11px] text-[#6b7280]">Fee receipt · sample</p>
          </div>
        </div>
        {sealUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={sealUrl} alt="Official seal" className="size-12 object-contain opacity-90" />
        ) : null}
      </div>
      <div className="mt-4 space-y-2">
        <div className="flex justify-between text-[12px]">
          <span className="text-[#6b7280]">Receipt no.</span>
          <span className="font-medium text-[#111827]">FY-2026-00482</span>
        </div>
        <div className="flex justify-between text-[12px]">
          <span className="text-[#6b7280]">Amount</span>
          <span className="font-semibold" style={{ color: primaryColor }}>
            ₹ 42,500
          </span>
        </div>
      </div>
    </div>
  );
}

export function BrandingPortalPreviewDialog({
  open,
  data,
  formValues,
  onClose,
}: {
  open: boolean;
  data: InstitutionBrandingPage | null;
  formValues: InstitutionBrandingFormValues;
  onClose: () => void;
}) {
  if (!data) return null;

  const displayName = String(formValues.display_name ?? "College");
  const primaryColor = formValues.primary_color || "#245dd8";
  const secondaryColor = formValues.secondary_color || "#64748b";
  const textOnPrimary = formValues.text_on_primary || "#ffffff";
  const logoWhite =
    data.brand_assets.find((a) => a.asset_key === "logo_white")?.file_id ??
    data.primary_logo.file_id;
  const sealFileId =
    data.brand_assets.find((a) => a.asset_key === "official_seal")?.file_id ?? null;

  const uploadedAssets = data.brand_assets.filter((a) => a.file_id);

  return (
    <PreviewDialogShell
      open={open}
      title="Branding preview"
      subtitle="How logos, colours and templates appear across portals and documents."
      onClose={onClose}
      wide
    >
      <div className="space-y-8">
        <section>
          <h3 className="mb-3 text-[12px] font-semibold uppercase tracking-wide text-[#9ca3af]">
            Live placements
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            {data.preview_items.map((item) => (
              <div
                key={item.title}
                className="rounded-lg border border-[#f1f5f9] bg-[#fafbfc] px-3 py-2"
              >
                <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
                <p className="text-[12px] text-[#6b7280]">{item.description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <div>
            <h3 className="mb-3 text-[13px] font-semibold text-[#111827]">Student portal header</h3>
            <PortalHeaderMock
              displayName={displayName}
              primaryColor={primaryColor}
              textOnPrimary={textOnPrimary}
              logoFileId={logoWhite}
            />
          </div>
          <div>
            <h3 className="mb-3 text-[13px] font-semibold text-[#111827]">Fee receipt</h3>
            <FeeReceiptMock
              displayName={displayName}
              primaryColor={primaryColor}
              logoFileId={data.primary_logo.file_id}
              sealFileId={sealFileId}
            />
          </div>
        </section>

        <section>
          <h3 className="mb-3 text-[13px] font-semibold text-[#111827]">Brand colours</h3>
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2 rounded-lg border border-[#e8ecf2] px-3 py-2">
              <span className="size-8 rounded-md border" style={{ backgroundColor: primaryColor }} />
              <div>
                <p className="text-[12px] font-medium text-[#111827]">Primary</p>
                <p className="font-mono text-[11px] text-[#6b7280]">{primaryColor}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 rounded-lg border border-[#e8ecf2] px-3 py-2">
              <span
                className="size-8 rounded-md border"
                style={{ backgroundColor: secondaryColor }}
              />
              <div>
                <p className="text-[12px] font-medium text-[#111827]">Secondary</p>
                <p className="font-mono text-[11px] text-[#6b7280]">{secondaryColor}</p>
              </div>
            </div>
          </div>
        </section>

        <section>
          <h3 className="mb-3 text-[13px] font-semibold text-[#111827]">Uploaded brand assets</h3>
          <AssetsPreviewGrid assets={uploadedAssets} primaryLogoId={data.primary_logo.file_id} />
        </section>

        <section>
          <h3 className="mb-3 text-[13px] font-semibold text-[#111827]">Document templates</h3>
          <TemplatesPreviewList rows={data.document_templates} />
        </section>
      </div>
    </PreviewDialogShell>
  );
}

function AssetsPreviewGrid({
  assets,
  primaryLogoId,
}: {
  assets: BrandingAssetRow[];
  primaryLogoId: string | null;
}) {
  const rows = assets.length
    ? assets
    : primaryLogoId
      ? [
          {
            asset_key: "primary_logo",
            label: "Primary logo",
            detail_line: "",
            status: "uploaded",
            status_label: "Uploaded",
            editable: false,
            file_name: null,
            file_id: primaryLogoId,
          } satisfies BrandingAssetRow,
        ]
      : [];

  if (!rows.length) {
    return <p className="text-[13px] text-[#9ca3af]">Upload logos and assets to see them here.</p>;
  }

  return (
    <ul className="grid gap-3 sm:grid-cols-2">
      {rows.map((row) => (
        <li
          key={row.asset_key}
          className="flex gap-3 rounded-xl border border-[#e8ecf2] bg-[#fafbfc] p-3"
        >
          <BrandingImagePreview fileId={row.file_id} alt={row.label} className="size-20 shrink-0" />
          <div className="min-w-0 flex-1">
            <p className="text-[13px] font-medium text-[#111827]">{row.label}</p>
            <p className="mt-0.5 text-[11px] leading-snug text-[#6b7280]">{row.detail_line}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}

function TemplatesPreviewList({ rows }: { rows: BrandingDocumentTemplateRow[] }) {
  return (
    <ul className="divide-y divide-[#f1f5f9] rounded-xl border border-[#e8ecf2] bg-white">
      {rows.map((row) => (
        <li
          key={row.template_key}
          className="flex flex-wrap items-center justify-between gap-2 px-4 py-3"
        >
          <div>
            <p className="text-[13px] font-medium text-[#111827]">{row.title}</p>
            <p className="text-[12px] text-[#6b7280]">{row.used_for}</p>
          </div>
          <span className="rounded-full bg-[#fff7ed] px-2.5 py-0.5 text-[11px] font-medium text-[#c2410c]">
            {row.status_label}
          </span>
        </li>
      ))}
    </ul>
  );
}