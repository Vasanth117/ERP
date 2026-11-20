"use client";

import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import { useInstitutionProfile } from "@/features/college-admin/hooks/use-institution";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "CA";
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase();
  return `${parts[0]![0] ?? ""}${parts[parts.length - 1]![0] ?? ""}`.toUpperCase();
}

export function CollegeAdminHeader() {
  const { data: user } = useCurrentUser();
  const { data: profile } = useInstitutionProfile();

  const displayName = user?.full_name ?? user?.email ?? "College Admin";
  const term =
    profile != null
      ? `${profile.locale} · ${profile.timezone}`
      : "AY loading…";

  return (
    <header
      className="flex h-[72px] shrink-0 items-center gap-4 border-b border-[#dce3ec] bg-white px-8"
      data-figma-node="64:189"
    >
      <div className="flex min-w-0 flex-1 items-center gap-2.5 rounded-md border border-[#dce3ec] px-3 py-2">
        <CollegeAdminIcon name="h-738bc" size={15} />
        <p className="min-w-0 flex-1 text-xs text-[#607086]">
          Search students, faculty, receipts, approvals…
        </p>
        <span className="text-[11px] text-[#8a98aa]">⌘ K</span>
      </div>

      <div className="flex items-center gap-1.5 rounded bg-[#eef1f5] px-2 py-1">
        <CollegeAdminIcon
          name="h-a05cf"
          size={6}
          className="size-1.5 shrink-0 fill-[#607086] text-[#607086]"
        />
        <span className="text-[11px] font-semibold text-[#607086]">{term}</span>
      </div>

      <button
        type="button"
        className="rounded p-1 hover:bg-[#f5f8ff]"
        aria-label="Notifications"
      >
        <CollegeAdminIcon name="h-ca0a6" size={18} />
      </button>

      <div className="flex items-center gap-2.5">
        <div className="flex size-8 items-center justify-center rounded-2xl bg-[#ebf2ff] text-[11px] font-semibold text-[#245dd8]">
          {initials(displayName)}
        </div>
        <div className="leading-tight">
          <p className="text-xs font-semibold text-[#172b45]">{displayName}</p>
          <p className="text-[10px] text-[#607086]">College Admin</p>
        </div>
        <CollegeAdminIcon name="h-4038e" size={14} />
      </div>
    </header>
  );
}