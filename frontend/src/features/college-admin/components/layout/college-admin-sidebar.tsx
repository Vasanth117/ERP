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
import { isCollegeAdminNavItemActive } from "@/features/college-admin/config/college-admin-nav-utils";
import { collegeAdminNavGroups } from "@/features/college-admin/config/navigation";
import { BenchlogoNameIcon } from "@/components/icons/erp/generated/benchlogo_name";
import { useCollegeAdminDemoMode } from "@/features/college-admin/context/college-admin-demo-mode-context";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { cn } from "@/lib/utils";

const STORAGE_COLLAPSED = "college-admin-sidebar-collapsed";
const WIDTH_EXPANDED = 264;
const WIDTH_COLLAPSED = 72;

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "CA";
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase();
  return `${parts[0]![0] ?? ""}${parts[parts.length - 1]![0] ?? ""}`.toUpperCase();
}

function formatRoleLabel(role: string | undefined): string {
  if (!role?.trim()) return "College Admin";
  return role
    .trim()
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

const NAV_ROW =
  "flex min-h-[38px] w-full items-center gap-2.5 rounded-[10px] text-[14px] leading-5 tracking-[-0.01em] transition-colors";
const NAV_ICON_SLOT = "flex size-5 shrink-0 items-center justify-center";

function SidebarToggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (next: boolean) => void;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative h-[22px] w-[40px] shrink-0 rounded-full transition-colors",
        checked ? "bg-[#245dd8]" : "bg-[#e2e8f0]",
      )}
    >
      <span
        className={cn(
          "absolute top-[3px] size-4 rounded-full bg-white shadow-[0_1px_3px_rgba(15,23,42,0.2)] transition-[left]",
          checked ? "left-[21px]" : "left-[3px]",
        )}
      />
    </button>
  );
}

export function CollegeAdminSidebar() {
  const pathname = usePathname();
  const { data: user } = useCurrentUser();
  const [profileOpen, setProfileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const { demoMode, setDemoMode } = useCollegeAdminDemoMode();
  const [canScrollMore, setCanScrollMore] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);
  const navRef = useRef<HTMLElement>(null);

  const displayName = user?.full_name ?? user?.email ?? "College Admin";
  const roleLabel = formatRoleLabel(user?.role);

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

  useEffect(() => {
    if (!navRef.current || collapsed) return;
    const activeEl = navRef.current.querySelector<HTMLElement>("[data-nav-active='true']");
    activeEl?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [pathname, collapsed]);

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
    () => collegeAdminNavGroups.flatMap((group) => group.items),
    [],
  );

  const isNavItemActive = useCallback(
    (item: (typeof flatNavItems)[number]) => isCollegeAdminNavItemActive(pathname, item),
    [pathname],
  );

  return (
    <aside
      className="relative sticky top-0 flex h-screen shrink-0 flex-col overflow-visible border-r border-[#e8ecf2] bg-white transition-[width] duration-200 ease-in-out"
      style={{ width: collapsed ? WIDTH_COLLAPSED : WIDTH_EXPANDED }}
      data-figma-node="64:163"
      aria-expanded={!collapsed}
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
          "shrink-0 border-b border-[#e8ecf2]",
          collapsed ? "flex justify-center px-2 py-5" : "px-4 py-5",
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
          <CollegeAdminSidebarIcon name="backend-logo" size={collapsed ? 28 : 32} className="shrink-0" />
          {!collapsed ? <BenchlogoNameIcon width={118} height={22} /> : null}
        </Link>
      </div>

      <div className="relative min-h-0 flex-1">
        <nav
          ref={navRef}
          className={cn(
            "h-full overflow-y-auto overflow-x-hidden py-2 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden",
            collapsed ? "px-1.5" : "px-2.5",
            canScrollMore && !collapsed ? "pb-12" : undefined,
          )}
        >
          {collapsed
            ? flatNavItems.map((item) => {
                const active = isNavItemActive(item);
                return (
                  <Link
                    key={item.id}
                    href={item.href}
                    title={item.label}
                    aria-current={active ? "page" : undefined}
                    data-nav-active={active ? "true" : undefined}
                    className={cn(
                      NAV_ROW,
                      "mb-0.5 justify-center px-2",
                      active
                        ? "bg-[#eef4ff] text-[#245dd8] ring-1 ring-inset ring-[#c9d9f7]"
                        : "text-[#4b5563] hover:bg-[#f8fafc]",
                    )}
                  >
                    <CollegeAdminSidebarIcon name={item.icon} size={20} active={active} />
                  </Link>
                );
              })
            : collegeAdminNavGroups.map((group) => {
                const groupActive = group.items.some((item) => isNavItemActive(item));
                return (
                <div key={group.title} className="mb-1">
                  <p
                    className={cn(
                      "px-3 pb-1 pt-3 text-[10px] font-semibold uppercase tracking-[0.04em]",
                      groupActive ? "text-[#245dd8]" : "text-[#8a94a3]",
                    )}
                  >
                    {group.title}
                  </p>
                  <ul className="flex flex-col gap-0.5">
                    {group.items.map((item) => {
                      const active = isNavItemActive(item);
                      return (
                        <li key={item.id}>
                          <Link
                            href={item.href}
                            aria-current={active ? "page" : undefined}
                            data-nav-active={active ? "true" : undefined}
                            className={cn(
                              NAV_ROW,
                              "px-3",
                              active
                                ? "bg-[#eef4ff] font-semibold text-[#245dd8] ring-1 ring-inset ring-[#c9d9f7]"
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
                </div>
              );
              })}
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
          "relative shrink-0 border-t border-[#e8ecf2] bg-white",
          collapsed ? "px-2 py-2" : "px-3 py-3",
        )}
        ref={profileRef}
      >
        {!collapsed ? (
          <div className="flex items-center justify-between gap-2 border-b border-[#f1f5f9] px-1 py-2.5">
            <span className="text-[13px] font-medium text-[#374151]">Demo mode</span>
            <SidebarToggle
              checked={demoMode}
              onChange={setDemoMode}
              label="Demo mode"
            />
          </div>
        ) : null}

        {collapsed ? (
          <div className="flex flex-col items-center gap-2">
            <SidebarToggle
              checked={demoMode}
              onChange={setDemoMode}
              label="Demo mode"
            />
            <button
              type="button"
              title={displayName}
              className="flex size-10 items-center justify-center overflow-hidden rounded-full bg-[#eef4ff] text-[13px] font-semibold text-[#245dd8]"
              onClick={() => setProfileOpen((v) => !v)}
            >
              {initials(displayName)}
            </button>
            {profileOpen ? (
              <div className="absolute bottom-2 left-[calc(100%+8px)] z-50 w-52 rounded-xl border border-[#e8ecf2] bg-white p-2 shadow-lg">
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
          </div>
        ) : (
          <>
            <button
              type="button"
              className="mt-2 flex w-full items-center gap-3 rounded-xl border border-[#e8ecf2] bg-white p-3 text-left shadow-[0_1px_2px_rgba(15,23,42,0.04)] transition-colors hover:bg-[#f8fafc]"
              onClick={() => setProfileOpen((v) => !v)}
            >
              <div className="flex size-10 shrink-0 items-center justify-center overflow-hidden rounded-full bg-[#eef4ff] text-[12px] font-semibold text-[#245dd8]">
                {initials(displayName)}
              </div>
              <span className="min-w-0 flex-1 leading-snug">
                <span className="block truncate text-[14px] font-semibold text-[#111827]">
                  {displayName}
                </span>
                <span className="mt-0.5 block truncate text-[12px] font-normal text-[#94a3b8]">
                  {roleLabel}
                </span>
              </span>
              <CollegeAdminChevronDown
                className={cn(
                  "size-4 shrink-0 text-[#9ca3af] transition-transform",
                  profileOpen && "rotate-180",
                )}
                aria-hidden
              />
            </button>
            {profileOpen ? (
              <div className="mt-2 space-y-0.5 border-t border-[#f1f5f9] pt-2 text-[13px] font-normal">
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
          </>
        )}
      </div>
    </aside>
  );
}