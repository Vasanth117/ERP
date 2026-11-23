import { Label } from "@/components/ui/label";
import type { InstitutionFieldMeta } from "@/features/college-admin/types/institution";

/** Wraps a labeled field for scroll-to validation (`data-field-key`). */
export function CollegeAdminFormField({
  meta,
  children,
  fieldKey,
}: {
  meta?: InstitutionFieldMeta;
  children: React.ReactNode;
  /** Use when meta is absent but scrolling should still work. */
  fieldKey?: string;
}) {
  const key = meta?.key ?? fieldKey;
  if (!key && !meta) return <>{children}</>;
  return (
    <div className="space-y-1.5" data-field-key={key}>
      {meta ? (
        <Label className="text-[13px] font-medium text-[#374151]">
          {meta.label}
          {meta.required ? <span className="text-[#dc2626]"> *</span> : null}
        </Label>
      ) : null}
      {children}
    </div>
  );
}