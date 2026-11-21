"use client";

import { cn } from "@/lib/utils";

export type ProfileUpdateRequestTab = "request" | "status";

type ProfileUpdateRequestTabsProps = {
  value: ProfileUpdateRequestTab;
  onChange: (value: ProfileUpdateRequestTab) => void;
};

export function ProfileUpdateRequestTabs({ value, onChange }: ProfileUpdateRequestTabsProps) {
  return (
    <div
      className="mb-5 grid grid-cols-2 gap-1.5 rounded-lg border border-[#e3e9f2] bg-[#f8fafc] p-1"
      role="tablist"
      aria-label="Profile update requests"
    >
      {(
        [
          { id: "request" as const, label: "Update request" },
          { id: "status" as const, label: "Request status" },
        ] as const
      ).map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={value === tab.id}
          onClick={() => onChange(tab.id)}
          className={cn(
            "rounded-md py-2 text-[14px] font-medium transition-all",
            value === tab.id
              ? "border border-[#e3e9f2] bg-white text-[#245dd8] shadow-sm"
              : "border border-transparent text-[#64748b] hover:text-[#172b45]",
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}