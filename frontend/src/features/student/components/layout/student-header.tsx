"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { studentNavFlat, studentNavItemByHref } from "@/features/student/config/navigation";

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "ST";
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase();
  return `${parts[0]![0] ?? ""}${parts[parts.length - 1]![0] ?? ""}`.toUpperCase();
}

function navActive(pathname: string, href: string): boolean {
  return pathname === href || (href !== "/student/dashboard" && pathname.startsWith(`${href}/`));
}

export function StudentSidebarBrand() {
  return (
    <div className="flex items-center gap-3 px-3 py-1">
      <div className="flex size-9 items-center justify-center rounded-lg bg-[#eff6ff]">
        <CollegeAdminIcon name="graduation-cap" size={20} className="text-[#245dd8]" />
      </div>
      <div>
        <p className="text-[14px] font-semibold leading-tight text-[#111827]">University</p>
        <p className="text-[11px] text-[#6b7280]">Student Portal</p>
      </div>
    </div>
  );
}

export function StudentHeader() {
  const pathname = usePathname() ?? "/student/dashboard";
  const { data: user } = useCurrentUser();
  const nav =
    studentNavItemByHref(pathname) ??
    studentNavFlat.find((item) => navActive(pathname, item.href));

  const today = new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(new Date());

  const displayName = user?.full_name ?? user?.email ?? "Student";

  return (
    <header className="sticky top-0 z-20 flex h-[72px] shrink-0 items-center justify-between gap-4 border-b border-[#e8ecf2] bg-white px-6 md:px-8">
      <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-2 text-[14px] text-[#607086]">
        <Link href="/student/home" className="flex items-center text-[#245dd8] hover:opacity-80">
          <CollegeAdminIcon name="house" size={15} className="text-[#245dd8]" />
          <span className="sr-only">Home</span>
        </Link>
        <CollegeAdminIcon name="chevron-right" size={12} className="text-[#9ca3af]" />
        <span className="truncate font-medium text-[#111827]">{nav?.label ?? "Student Portal"}</span>
      </nav>
      <div className="flex items-center gap-4 text-sm text-[#607086]">
        <span className="hidden sm:inline">{today}</span>
        <Link
          href="/student/dashboard"
          className="flex size-9 items-center justify-center rounded-lg border border-[#e8ecf2] text-[#607086] hover:bg-[#f8fafc]"
          aria-label="Notifications on dashboard"
        >
          <CollegeAdminIcon name="bell" size={18} />
        </Link>
        <div
          className="flex size-8 items-center justify-center rounded-full bg-[#eff6ff] text-[11px] font-semibold text-[#1d4ed8]"
          title={displayName}
        >
          {initials(displayName)}
        </div>
      </div>
    </header>
  );
}