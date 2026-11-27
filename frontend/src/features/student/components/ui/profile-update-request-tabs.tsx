"use client";

import { cn } from "@/lib/utils";

export type ProfileUpdateRequestTab = "request" | "status";

type ProfileUpdateRequestTabsProps = {
  value: ProfileUpdateRequestTab;
  onChange: (value: ProfileUpdateRequestTab) => void;
};

/** Secondary tabs — underline style only (no boxed segment). */
export function ProfileUpdateRequestTabs({ value, onChange }: ProfileUpdateRequestTabsProps) {
  return (
    <nav className="border-b border-[#e8ecf2]" aria-label="Profile update request views">
      <div className="-mb-px flex flex-wrap gap-x-5">
        {(
          [
            { id: "request" as const, label: "Update request" },
            { id: "status" as const, label: "Request status" },
          ] as const
        ).map((tab) => {
          const active = value === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => onChange(tab.id)}
              className={cn(
                "relative shrink-0 whitespace-nowrap border-b-2 px-0.5 pb-2.5 pt-0.5 text-[14px] font-medium leading-5 tracking-[-0.01em] transition-colors duration-150",
                active
                  ? "border-[#245dd8] text-[#245dd8]"
                  : "border-transparent text-[#6b7280] hover:border-[#d1d5db] hover:text-[#111827]",
              )}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
    </nav>
  );
}