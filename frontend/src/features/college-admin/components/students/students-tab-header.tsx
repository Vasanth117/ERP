import type { ReactNode } from "react";

export function StudentsTabHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0">
        <h2 className="text-[16px] font-semibold text-[#111827]">{title}</h2>
        {subtitle ? <p className="mt-0.5 text-[13px] text-[#6b7280]">{subtitle}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}