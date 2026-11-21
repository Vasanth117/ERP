"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { BenchlogoNameIcon } from "@/components/icons/erp/generated/benchlogo_name";
import { CollegeAdminSidebarIcon } from "@/features/college-admin/components/layout/college-admin-sidebar-icon";
import {
  CollegeAdminChevronDown,
  CollegeAdminChevronLeft,
  CollegeAdminChevronRight,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { useStudentProfile } from "@/features/student/hooks/use-student-profile";
import {
  sidebarNavActive,
  studentSidebarNav,
} from "@/features/student/config/sidebar-navigation";
import {
  PORTAL_NAV_GROUP_LABEL,
  PORTAL_NAV_ICON_SLOT,
  PORTAL_NAV_ROW,
  PORTAL_SURFACE_BORDER,
} from "@/lib/portal/shell-styles";
import { cn } from "@/lib/utils";

const STORAGE_COLLAPSED = "student-sidebar-collapsed";
const WIDTH_EXPANDED = 264;
const WIDTH_COLLAPSED = 72;

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "ST";
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase();
  return `${parts[0]![0] ?? ""}${parts[parts.length - 1]![0] ?? ""}`.toUpperCase();
}

export function StudentSidebar() {
  const pathname = usePathname() ?? "";
  const { data: user } = useCurrentUser();
  const { data: profile } = useStudentProfile();

  const [profileOpen, setProfileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [canScrollMore, setCanScrollMore] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);
  const navRef = useRef<HTMLElement>(null);

  const displayName = profile?.full_name ?? user?.full_name ?? "Student";
  const roleLabel = [profile?.roll_number, "Student"].filter(Boolean).join(" · ");

  useEffect(() => {
    try {
      if (localStorage.getItem(STORAGE_COLLAPSED) === "1") setCollapsed(true);
    } catch {
      /* ignore */
    }
  }, []);

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

  const updateScrollHint = useCallback(() => {
    const el = navRef.current;
    if (!el) return;
    setCanScrollMore(el.scrollHeight - el.scrollTop - el.clientHeight > 12);
  }, []);

  useEffect(() => {
    const el = navRef.current;
    if (!el) return;
    updateScrollHint();
    el.addEventListener("scroll", updateScrollHint, { passive: true });
    const ro = new ResizeObserver(() => updateScrollHint());
    ro.observe(el);
    return () => {
      el.removeEventListener("scroll", updateScrollHint);
      ro.disconnect();
    };
  }, [collapsed, updateScrollHint]);

  const setSidebarCollapsed = useCallback((next: boolean) => {
    setCollapsed(next);
    try {
      localStorage.setItem(STORAGE_COLLAPSED, next ? "1" : "0");
    } catch {
      /* ignore */
    }
    if (next) setProfileOpen(false);
  }, []);

  const toggleCollapsed = useCallback(() => {
    setSidebarCollapsed(!collapsed);
  }, [collapsed, setSidebarCollapsed]);

  const scrollNavFurther = useCallback(() => {
    navRef.current?.scrollBy({ top: 160, behavior: "smooth" });
  }, []);

  const flatNavItems = useMemo(
    () => studentSidebarNav.flatMap((group) => group.items),
    [],
  );

  return (
    <aside
      className={cn(
        "relative sticky top-0 flex h-screen shrink-0 flex-col overflow-visible border-r bg-white transition-[width] duration-200 ease-in-out",
        PORTAL_SURFACE_BORDER,
      )}
      style={{ width: collapsed ? WIDTH_COLLAPSED : WIDTH_EXPANDED }}
      data-figma-node="163:3"
      aria-expanded={!collapsed}
      aria-label="Student portal navigation"
    >
      <button
        type="button"
        onClick={toggleCollapsed}
        className="absolute top-[22px] -right-3.5 z-30 flex size-7 items-center justify-center rounded-lg border border-[#e5e7eb] bg-white text-[#374151] shadow-[0_1px_4px_rgba(15,23,42,0.12)] transition-colors hover:bg-[#f9fafb]"
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
          "shrink-0 border-b",
          PORTAL_SURFACE_BORDER,
          collapsed ? "flex justify-center px-2 py-5" : "px-4 py-5",
        )}
      >
        <Link
          href="/student/dashboard"
          className={cn("flex max-w-full items-center", collapsed ? "justify-center" : "gap-2.5")}
          title={collapsed ? "Student Portal" : undefined}
        >
          <CollegeAdminSidebarIcon name="backend-logo" size={collapsed ? 28 : 32} className="shrink-0" />
          {!collapsed ? (
            <span className="flex min-w-0 flex-col gap-0.5">
              <BenchlogoNameIcon width={118} height={22} />
              <span className="text-[10px] font-semibold uppercase tracking-[0.06em] text-[#8a94a3]">
                Student Portal
              </span>
            </span>
          ) : null}
        </Link>
      </div>

      <div className="relative min-h-0 flex-1">
        <nav
          ref={navRef}
          className={cn(
            "h-full overflow-y-auto overflow-x-hidden py-2 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden",
            collapsed ? "px-1.5" : "px-2.5",
          )}
        >
          {collapsed
            ? flatNavItems.map((item) => {
                const active = sidebarNavActive(pathname, item.href);
                return (
                  <Link
                    key={item.id}
                    href={item.href}
                    title={item.label}
                    className={cn(
                      PORTAL_NAV_ROW,
                      "mb-0.5 justify-center px-2",
                      active
                        ? "bg-[#eef4ff] text-[#245dd8]"
                        : "text-[#4b5563] hover:bg-[#f8fafc]",
                    )}
                  >
                    <CollegeAdminSidebarIcon name={item.icon} size={20} active={active} />
                  </Link>
                );
              })
            : studentSidebarNav.map((group) => (
                <div key={group.title} className="mb-1">
                  <p className={PORTAL_NAV_GROUP_LABEL}>{group.title}</p>
                  <ul className="flex flex-col gap-0.5">
                    {group.items.map((item) => {
                      const active = sidebarNavActive(pathname, item.href);
                      return (
                        <li key={item.id}>
                          <Link
                            href={item.href}
                            data-figma-node={item.figmaNode}
                            className={cn(
                              PORTAL_NAV_ROW,
                              "px-3",
                              active
                                ? "bg-[#eef4ff] font-medium text-[#245dd8]"
                                : "font-normal text-[#4b5563] hover:bg-[#f8fafc]",
                            )}
                          >
                            <span className={PORTAL_NAV_ICON_SLOT}>
                              <CollegeAdminSidebarIcon name={item.icon} size={20} active={active} />
                            </span>
                            <span className="min-w-0 flex-1 truncate">{item.label}</span>
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ))}
        </nav>

        {canScrollMore && !collapsed ? (
          <div className="pointer-events-none absolute inset-x-0 bottom-0 flex justify-center bg-gradient-to-t from-white via-white/90 to-transparent pb-2 pt-8">
            <button
              type="button"
              onClick={scrollNavFurther}
              className="pointer-events-auto flex items-center gap-1 rounded-full border border-[#e8ecf2] bg-white px-3 py-1.5 text-[11px] font-medium text-[#4b5563] shadow-[0_4px_14px_rgba(15,23,42,0.08)] transition-colors hover:bg-[#f8fafc]"
            >
              Scroll for more
              <CollegeAdminChevronDown className="size-3.5 text-[#9ca3af]" aria-hidden />
            </button>
          </div>
        ) : null}
      </div>

      <div
        className={cn(
          "relative shrink-0 border-t bg-white",
          PORTAL_SURFACE_BORDER,
          collapsed ? "px-2 py-2" : "px-3 py-3",
        )}
        ref={profileRef}
      >
        {collapsed ? (
          <button
            type="button"
            title={displayName}
            className="mx-auto flex size-10 items-center justify-center overflow-hidden rounded-full bg-[#eef4ff] text-[13px] font-semibold text-[#245dd8]"
            onClick={() => setProfileOpen((v) => !v)}
          >
            {initials(displayName)}
          </button>
        ) : (
          <button
            type="button"
            className="flex w-full items-center gap-3 rounded-xl border border-[#e8ecf2] bg-white p-3 text-left shadow-[0_1px_2px_rgba(15,23,42,0.04)] transition-colors hover:bg-[#f8fafc]"
            onClick={() => setProfileOpen((v) => !v)}
          >
            <div className="flex size-10 shrink-0 items-center justify-center overflow-hidden rounded-full bg-[#eef4ff] text-[12px] font-semibold text-[#245dd8]">
              {initials(displayName)}
            </div>
            <span className="min-w-0 flex-1 leading-snug">
              <span className="block truncate text-[14px] font-semibold text-[#111827]">{displayName}</span>
              <span className="mt-0.5 block truncate text-[12px] font-normal text-[#94a3b8]">{roleLabel}</span>
            </span>
            <CollegeAdminChevronDown
              className={cn("size-4 shrink-0 text-[#9ca3af] transition-transform", profileOpen && "rotate-180")}
              aria-hidden
            />
          </button>
        )}

        {profileOpen ? (
          <div
            className={cn(
              "space-y-0.5 border-t border-[#f1f5f9] pt-2 text-[13px] font-normal",
              collapsed
                ? "absolute bottom-2 left-[calc(100%+8px)] z-50 w-52 rounded-xl border border-[#e8ecf2] bg-white p-2 shadow-lg"
                : "mt-2",
            )}
          >
            <Link
              href="/student/profile"
              className="block rounded-lg px-2 py-2 text-[#4b5563] hover:bg-[#f8fafc]"
              onClick={() => setProfileOpen(false)}
            >
              My profile
            </Link>
            <Link
              href="/"
              className="block rounded-lg px-2 py-2 text-[#4b5563] hover:bg-[#f8fafc]"
              onClick={() => setProfileOpen(false)}
            >
              Module launcher
            </Link>
            <Link
              href="/login?portal=student-performance&next=%2Fstudent%2Fdashboard"
              className="block rounded-lg px-2 py-2 text-[#4b5563] hover:bg-[#f8fafc]"
              onClick={() => setProfileOpen(false)}
            >
              Switch account
            </Link>
          </div>
        ) : null}
      </div>
    </aside>
  );
}