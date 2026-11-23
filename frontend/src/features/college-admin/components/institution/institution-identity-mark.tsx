"use client";

import Link from "next/link";

import { LandmarkIcon } from "@/components/icons/erp/generated/landmark";
import { useInstitutionBrandingLogoUrl } from "@/features/college-admin/hooks/use-institution-branding-logo";
import { cn } from "@/lib/utils";

type InstitutionIdentityMarkProps = {
  displayName: string;
  logoFileId: string | null | undefined;
  accent: string;
  className?: string;
  size?: "md" | "lg";
  showUploadHint?: boolean;
};

export function InstitutionIdentityMark({
  displayName,
  logoFileId,
  accent,
  className,
  size = "lg",
  showUploadHint = false,
}: InstitutionIdentityMarkProps) {
  const logoUrl = useInstitutionBrandingLogoUrl(logoFileId);
  const dim = size === "lg" ? "size-20" : "size-16";
  const iconSize = size === "lg" ? "size-9" : "size-8";

  const frame = (
    <div
      className={cn(
        "flex shrink-0 items-center justify-center overflow-hidden rounded-xl border bg-white shadow-sm",
        dim,
        className,
      )}
      style={{
        borderColor: `${accent}33`,
        boxShadow: `0 1px 2px rgba(15,23,42,0.04), 0 0 0 1px ${accent}14`,
      }}
    >
      {logoUrl ? (
        // eslint-disable-next-line @next/next/no-img-element -- authenticated blob URL
        <img
          src={logoUrl}
          alt={`${displayName} logo`}
          className="max-h-[calc(100%-10px)] max-w-[calc(100%-10px)] object-contain"
        />
      ) : (
        <div
          className="flex size-full items-center justify-center text-white"
          style={{ backgroundColor: accent }}
        >
          <LandmarkIcon className={iconSize} aria-hidden />
        </div>
      )}
    </div>
  );

  if (!logoUrl && showUploadHint) {
    return (
      <Link
        href="/college-admin/institution/branding"
        className="group shrink-0 rounded-xl outline-offset-2 focus-visible:outline-2 focus-visible:outline-[#245dd8]"
        title="Upload college logo"
      >
        {frame}
        <span className="mt-1.5 block text-center text-[10px] font-medium text-[#245dd8] opacity-0 transition-opacity group-hover:opacity-100">
          Add logo
        </span>
      </Link>
    );
  }

  return frame;
}