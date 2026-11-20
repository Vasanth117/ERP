"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CollegeAdminSidebarIcon } from "@/features/college-admin/components/layout/college-admin-sidebar-icon";
import {
  CollegeAdminChevronDown,
  CollegeAdminChevronLeft,
  CollegeAdminChevronRight,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  collegeAdminNavGroups,
  type CollegeAdminNavGroup,
} from "@/features/college-admin/config/navigation";
import { BenchlogoNameIcon } from "@/components/icons/erp/generated/benchlogo_name";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { cn } from "@/lib/utils";

const STORAGE_KEY = "college-admin-sidebar-collapsed";
const WIDTH_EXPANDED = 252;
const WIDTH_COLLAPSED = 72;

function navActive(pathname: string, href: string): boolean {
  if (href === "/college-admin/dashboard") {
    return pathname === href || pathname.startsWith(`${href}/`);
  }
  if (href.startsWith("/college-admin/institution")) {
    return pathname.startsWith("/college-admin/institution");
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

function groupContainsActive(pathname: string, group: CollegeAdminNavGroup): boolean {
  return group.items.some((item) => navActive(pathname, item.href));
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "CA";
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase();
  return `${parts[0]![0] ?? ""}${parts[parts.length - 1]![0] ?? ""}`.toUpperCase();
}

function groupLabel(title: string): string {
  return title.charAt(0) + title.slice(1).toLowerCase();
}

const NAV_ROW =
  "flex min-h-[42px] w-full items-center gap-2.5 rounded-[10px] text-[14px] leading-5 tracking-[-0.01em] transition-colors";
const NAV_ICON_SLOT = "flex size-5 shrink-0 items-center justify-center";

export function CollegeAdminSidebar() {
  const pathname = usePathname();
  const { data: user } = useCurrentUser();
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [profileOpen, setProfileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  const displayName = user?.full_name ?? user?.email ?? "College Admin";
  const email = user?.email ?? "—";
  const defaultExpanded = useMemo(() => {
    const next: Record<string, boolean> = {};
    for (const group of collegeAdminNavGroups) {
      next[group.title] = groupContainsActive(pathname, group);
    }
    return next;
  }, [pathname]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === "1") setCollapsed(true);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    setExpanded((prev) => {
      const merged = { ...prev };
      for (const [key, val] of Object.entries(defaultExpanded)) {
        if (val) merged[key] = true;
      }
      return merged;
    });
  }, [defaultExpanded]);

  useEffect(() => {
    if (!profileOpen) return;
    const onPointerDown = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, [profileOpen]);

  const toggleGroup = useCallback((title: string) => {
    setExpanded((prev) => ({ ...prev, [title]: !prev[title] }));
  }, []);

  const setSidebarCollapsed = useCallback((next: boolean) => {
    setCollapsed(next);
    try {
      localStorage.setItem(STORAGE_KEY, next ? "1" : "0");
    } catch {
      /* ignore */
    }
    if (next) setProfileOpen(false);
  }, []);

  const toggleCollapsed = useCallback(() => {
    setSidebarCollapsed(!collapsed);
  }, [collapsed, setSidebarCollapsed]);

  const expandSidebarForGroup = useCallback(
    (title: string) => {
      setSidebarCollapsed(false);
      setExpanded((prev) => ({ ...prev, [title]: true }));
    },
    [setSidebarCollapsed],
  );

  return (
    <aside
      className="relative flex shrink-0 flex-col overflow-visible border-r border-[#e8ecf2] bg-white transition-[width] duration-200 ease-in-out"
      style={{ width: collapsed ? WIDTH_COLLAPSED : WIDTH_EXPANDED }}
      data-figma-node="64:163"
      aria-expanded={!collapsed}
    >
      <button
        type="button"
        onClick={toggleCollapsed}
        className="absolute top-[26px] -right-3.5 z-30 flex size-7 items-center justify-center rounded-lg border border-[#e5e7eb] bg-white text-[#374151] shadow-[0_1px_4px_rgba(15,23,42,0.12)] transition-colors hover:bg-[#f9fafb]"
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {collapsed ? (
          <CollegeAdminChevronRight className="size-4" aria-hidden />
        ) : (
          <CollegeAdminChevronLeft className="size-4" aria-hidden />
        )}
      </button>

      <div
        className={cn(
          "overflow-hidden border-b border-[#e8ecf2]",
          collapsed ? "flex justify-center px-2 py-4" : "px-4 py-5",
        )}
      >
        <Link
          href="/college-admin/dashboard"
          className={cn(
            "flex max-w-full items-center",
            collapsed ? "justify-center" : "gap-2.5",
          )}
          title={collapsed ? "benchend" : undefined}
        >
          <CollegeAdminSidebarIcon
            name="backend-logo"
            size={collapsed ? 26 : 28}
            className="shrink-0"
          />
          {!collapsed ? <BenchlogoNameIcon /> : null}
        </Link>
      </div>

      <nav
        className={cn(
          "flex flex-1 flex-col gap-0.5 overflow-y-auto py-3",
          collapsed ? "items-center px-1.5" : "px-2.5",
        )}
      >
        {collapsed
          ? collegeAdminNavGroups.map((group) => {
              const hasActive = groupContainsActive(pathname, group);
              return (
                <button
                  key={group.title}
                  type="button"
                  title={groupLabel(group.title)}
                  onClick={() => expandSidebarForGroup(group.title)}
                  className={cn(
                    NAV_ROW,
                    "w-full justify-center px-2",
                    hasActive
                      ? "bg-[#eef4ff] text-[#245dd8]"
                      : "text-[#4b5563] hover:bg-[#f8fafc]",
                  )}
                >
                  <CollegeAdminSidebarIcon name={group.icon} size={20} active={hasActive} />
                </button>
              );
            })
          : collegeAdminNavGroups.map((group) => {
              const open = expanded[group.title] ?? false;
              const hasActive = groupContainsActive(pathname, group);

              return (
                <div key={group.title} className="flex w-full flex-col gap-0.5">
                  <button
                    type="button"
                    onClick={() => toggleGroup(group.title)}
                    className={cn(
                      NAV_ROW,
                      "w-full px-3 text-left font-medium text-[#4b5563] hover:bg-[#f8fafc]",
                      hasActive && "text-[#245dd8]",
                    )}
                  >
                    <span className={NAV_ICON_SLOT}>
                      <CollegeAdminSidebarIcon
                        name={group.icon}
                        size={20}
                        active={hasActive}
                      />
                    </span>
                    <span className="min-w-0 flex-1 truncate">{groupLabel(group.title)}</span>
                    {open ? (
                      <CollegeAdminChevronDown
                        className="size-4 shrink-0 text-[#9ca3af]"
                        aria-hidden
                      />
                    ) : (
                      <CollegeAdminChevronRight
                        className="size-4 shrink-0 text-[#9ca3af]"
                        aria-hidden
                      />
                    )}
                  </button>
                  {open ? (
                    <ul className="flex flex-col gap-0.5 pb-0.5 pl-[30px] pr-0.5">
                      {group.items.map((item) => {
                        const active = navActive(pathname, item.href);
                        return (
                          <li key={item.id}>
                            <Link
                              href={item.href}
                              className={cn(
                                NAV_ROW,
                                "px-3",
                                active
                                  ? "bg-[#eef4ff] font-medium text-[#245dd8]"
                                  : "font-normal text-[#4b5563] hover:bg-[#f8fafc]",
                              )}
                            >
                              <span className={NAV_ICON_SLOT}>
                                <CollegeAdminSidebarIcon
                                  name={item.icon}
                                  size={20}
                                  active={active}
                                />
                              </span>
                              <span className="min-w-0 flex-1 truncate">{item.label}</span>
                            </Link>
                          </li>
                        );
                      })}
                    </ul>
                  ) : null}
                </div>
              );
            })}
      </nav>

      <div
        className={cn(
          "relative shrink-0 border-t border-[#e8ecf2] bg-white",
          collapsed ? "flex flex-col items-center gap-2 p-2" : "space-y-2 p-3",
        )}
        ref={profileRef}
      >
        {collapsed ? (
          <>
            <button
              type="button"
              title={displayName}
              className="flex size-10 items-center justify-center rounded-full bg-[#eef4ff] text-[13px] font-semibold text-[#245dd8]"
              onClick={() => setProfileOpen((v) => !v)}
            >
              {initials(displayName)}
            </button>
            {profileOpen ? (
              <div className="absolute bottom-2 left-[calc(100%+8px)] z-50 w-52 rounded-xl border border-[#e8ecf2] bg-white p-2 shadow-lg">
                <p className="truncate px-2 py-1 text-[12px] font-semibold text-[#111827]">
                  {displayName}
                </p>
                <p className="truncate px-2 pb-2 text-[11px] text-[#94a3b8]">{email}</p>
                <Link
                  href="/college-admin/institution/profile"
                  className="block rounded-lg px-2 py-2 text-[13px] text-[#4b5563] hover:bg-[#f8fafc]"
                >
                  Institution profile
                </Link>
                <Link
                  href="/"
                  className="block rounded-lg px-2 py-2 text-[13px] text-[#4b5563] hover:bg-[#f8fafc]"
                >
                  Module launcher
                </Link>
                <Link
                  href="/login"
                  className="block rounded-lg px-2 py-2 text-[13px] text-[#4b5563] hover:bg-[#f8fafc]"
                >
                  Switch account
                </Link>
              </div>
            ) : null}
          </>
        ) : (
          <>
            <div className="rounded-[12px] border border-[#e8ecf2] bg-white p-3 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <button
                type="button"
                className="flex w-full items-center gap-3 text-left"
                onClick={() => setProfileOpen((v) => !v)}
              >
                <div className="flex size-10 shrink-0 items-center justify-center overflow-hidden rounded-full bg-[#eef4ff] text-[13px] font-semibold text-[#245dd8]">
                  {initials(displayName)}
                </div>
                <div className="min-w-0 flex-1 leading-snug">
                  <p className="truncate text-[14px] font-semibold text-[#111827]">
                    {displayName}
                  </p>
                  <p className="truncate text-[12px] font-normal text-[#94a3b8]">{email}</p>
                  <p className="text-[11px] font-medium text-[#6b7280]">College Admin</p>
                </div>
                <CollegeAdminChevronDown
                  className={cn(
                    "size-4 shrink-0 text-[#9ca3af] transition-transform",
                    profileOpen && "rotate-180",
                  )}
                />
              </button>
              {profileOpen ? (
                <div className="mt-3 space-y-0.5 border-t border-[#f1f5f9] pt-2 text-[13px] font-normal">
                  <Link
                    href="/college-admin/institution/profile"
                    className="block rounded-lg px-2 py-2 text-[#4b5563] hover:bg-[#f8fafc]"
                  >
                    Institution profile
                  </Link>
                  <Link
                    href="/"
                    className="block rounded-lg px-2 py-2 text-[#4b5563] hover:bg-[#f8fafc]"
                  >
                    Module launcher
                  </Link>
                  <Link
                    href="/login"
                    className="block rounded-lg px-2 py-2 text-[#4b5563] hover:bg-[#f8fafc]"
                  >
                    Switch account
                  </Link>
                </div>
              ) : null}
            </div>
          </>
        )}
      </div>
    </aside>
  );
}