"use client";

import { cn } from "@/lib/utils";

export type LoginRole = "student" | "parent";

type LoginRoleTabsProps = {
  value: LoginRole;
  onChange: (value: LoginRole) => void;
};

export function LoginRoleTabs({ value, onChange }: LoginRoleTabsProps) {
  return (
    <div
      className="mb-4 grid grid-cols-2 gap-1.5 rounded-lg border border-[#e3e9f2] bg-[#f8fafc] p-1"
      role="tablist"
      aria-label="Sign in as"
    >
      {(["student", "parent"] as const).map((tab) => (
        <button
          key={tab}
          type="button"
          role="tab"
          aria-selected={value === tab}
          onClick={() => onChange(tab)}
          className={cn(
            "rounded-md py-2 text-[15px] font-medium transition-all",
            value === tab
              ? "border border-[#e3e9f2] bg-white text-[#245dd8] shadow-sm"
              : "border border-transparent text-[#64748b] hover:text-[#172b45]",
          )}
        >
          {tab === "student" ? "Student" : "Parent"}
        </button>
      ))}
    </div>
  );
}