"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import { CollegeAdminChevronDown } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  studentNavGroups,
  type StudentNavGroup,
} from "@/features/student/config/navigation";
import { StudentSidebarBrand } from "@/features/student/components/layout/student-header";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { cn } from "@/lib/utils";

const STORAGE_KEY = "student-sidebar-collapsed";

function navActive(pathname: string, href: string): boolean {
  if (href === "/student/home") {
    return pathname === "/student" || pathname === "/student/home";
  }
  if (href === "/student/dashboard") {
    return pathname === href;
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

function groupContainsActive(pathname: string, group: StudentNavGroup): boolean {
  return group.items.some((item) => navActive(pathname, item.href));
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "ST";
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase();
  return `${parts[0]![0] ?? ""}${parts[parts.length - 1]![0] ?? ""}`.toUpperCase();
}

const NAV_ROW =
  "flex min-h-[42px] w-full items-center gap-2.5 rounded-[10px] px-2.5 text-[14px] leading-5 tracking-[-0.01em] transition-colors";

export function StudentSidebar() {
  const pathname = usePathname() ?? "";
  const { data: user } = useCurrentUser();
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [collapsed, setCollapsed] = useState(false);

  const displayName = user?.full_name ?? user?.email ?? "Student";
  const roll = user?.email ?? "—";

  const portalHome = pathname === "/student/home" || pathname === "/student";

  const defaultExpanded = useMemo(() => {
    const next: Record<string, boolean> = {};
    for (const group of studentNavGroups) {
      next[group.title] = portalHome || groupContainsActive(pathname, group);
    }
    return next;
  }, [pathname, portalHome]);

  useEffect(() => {
    try {
      if (localStorage.getItem(STORAGE_KEY) === "1") setCollapsed(true);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    setExpanded((prev) => ({ ...defaultExpanded, ...prev }));
  }, [defaultExpanded]);

  const toggleGroup = useCallback((title: string) => {
    setExpanded((prev) => ({ ...prev, [title]: !prev[title] }));
  }, []);

  return (
    <aside
      className={cn(
        "flex shrink-0 flex-col border-r border-[#e8ecf2] bg-[#fafbfc] transition-[width] duration-200",
        collapsed ? "w-[72px]" : "w-[252px]",
      )}
    >
      <div className="border-b border-[#e8ecf2] px-3 py-5">
        {!collapsed ? <StudentSidebarBrand /> : (
          <div className="flex justify-center">
            <CollegeAdminIcon name="graduation-cap" size={22} className="text-[#245dd8]" />
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-4">
        {studentNavGroups.map((group) => {
          const open = expanded[group.title] ?? false;
          return (
            <div key={group.title} className="mb-2">
              {!collapsed ? (
                <button
                  type="button"
                  className="mb-1 flex w-full items-center justify-between px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-[#9ca3af]"
                  onClick={() => toggleGroup(group.title)}
                >
                  {group.title}
                  <CollegeAdminChevronDown
                    className={cn("size-3 transition-transform", open && "rotate-180")}
                  />
                </button>
              ) : null}
              {(collapsed || open) && (
                <ul className="flex flex-col gap-0.5">
                  {group.items.map((item) => {
                    const active = navActive(pathname, item.href);
                    return (
                      <li key={item.id}>
                        <Link
                          href={item.href}
                          title={item.label}
                          className={cn(
                            NAV_ROW,
                            active
                              ? "bg-white font-medium text-[#245dd8] shadow-[0_1px_2px_rgba(15,23,42,0.04)]"
                              : "text-[#4b5563] hover:bg-white/80",
                          )}
                        >
                          <CollegeAdminIcon
                            name={item.icon}
                            size={18}
                            className={active ? "text-[#245dd8]" : "text-[#636e7b]"}
                          />
                          {!collapsed ? <span className="truncate">{item.label}</span> : null}
                          {active && !collapsed ? (
                            <span className="ml-auto size-1 rounded-full bg-[#245dd8]" />
                          ) : null}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          );
        })}
      </div>

      <div className="border-t border-[#e8ecf2] p-3">
        {!collapsed ? (
          <div className="rounded-lg border border-[#e8ecf2] bg-white p-3 text-xs">
            <p className="font-medium text-[#111827]">{displayName}</p>
            <p className="mt-0.5 truncate text-[#9ca3af]">{roll}</p>
          </div>
        ) : (
          <div
            className="mx-auto flex size-9 items-center justify-center rounded-full bg-[#eff6ff] text-[10px] font-semibold text-[#1d4ed8]"
            title={displayName}
          >
            {initials(displayName)}
          </div>
        )}
      </div>
    </aside>
  );
}