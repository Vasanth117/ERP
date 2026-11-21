"use client";

import Link from "next/link";
import { useState, useRef, useEffect } from "react";

import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import { CollegeAdminChevronDown } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { useStudentDashboard } from "@/features/student/hooks/use-student-dashboard";
import { useStudentProfile } from "@/features/student/hooks/use-student-profile";
import { cn } from "@/lib/utils";

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "ST";
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase();
  return `${parts[0]![0] ?? ""}${parts[parts.length - 1]![0] ?? ""}`.toUpperCase();
}

/** Figma ST 00 — `ST / Top header` (node 163:156). */
export function StudentTopHeader() {
  const { data: user } = useCurrentUser();
  const dashboard = useStudentDashboard();
  const profile = useStudentProfile();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const term = dashboard.data?.academic_term;
  const studentProfile = profile.data;

  const displayName = studentProfile?.full_name ?? user?.full_name ?? "Student";
  const subtitle = [
    studentProfile?.roll_number,
    studentProfile?.programme_code ?? studentProfile?.department_name,
  ]
    .filter(Boolean)
    .join(" · ");

  useEffect(() => {
    if (!menuOpen) return;
    const onPointerDown = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, [menuOpen]);

  return (
    <header
      className="flex h-[72px] shrink-0 items-center gap-4 border-b border-[#e8ecf2] bg-white px-6 md:px-8"
      data-figma-node="163:156"
    >
      <label className="flex min-w-0 flex-1 items-center gap-2.5 rounded-md border border-[#e8ecf2] px-3 py-2">
        <CollegeAdminIcon name="h-738bc" size={15} className="shrink-0 text-[#607086]" />
        <span className="min-w-0 flex-1 text-xs text-[#607086]">
          Search subjects, results, assignments or notices…
        </span>
        <span className="hidden shrink-0 text-[11px] text-[#8a98aa] sm:inline">⌘ K</span>
      </label>

      <span className="inline-flex shrink-0 items-center gap-1.5 rounded bg-[#eef1f5] px-2 py-1 text-[11px] font-semibold text-[#607086]">
        <span className="size-1.5 rounded-full bg-[#607086]" aria-hidden />
        {term?.academic_year_label ?? "AY —"}
      </span>

      <span className="inline-flex shrink-0 items-center gap-1.5 rounded bg-[#ebf2ff] px-1.5 py-0.5 text-[11px] font-semibold text-[#245dd8]">
        <span className="size-1.5 rounded-full bg-[#245dd8]" aria-hidden />
        {term?.semester_label ?? "Semester —"}
      </span>

      <Link
        href="/student/dashboard"
        className="rounded p-1 hover:bg-[#f5f8ff]"
        aria-label="Notifications"
      >
        <CollegeAdminIcon name="h-ca0a6" size={18} className="text-[#607086]" />
      </Link>

      <div className="relative shrink-0" ref={menuRef}>
        <button
          type="button"
          className="flex items-center gap-2.5"
          onClick={() => setMenuOpen((v) => !v)}
          aria-expanded={menuOpen}
        >
          <div className="flex size-8 items-center justify-center rounded-2xl bg-[#ebf2ff] text-[11px] font-semibold text-[#245dd8]">
            {initials(displayName)}
          </div>
          <span className="hidden text-left sm:block">
            <span className="block text-xs font-semibold text-[#172b45]">{displayName}</span>
            <span className="block text-[10px] text-[#607086]">{subtitle || "Student"}</span>
          </span>
          <CollegeAdminChevronDown
            className={cn("size-3.5 text-[#607086] transition-transform", menuOpen && "rotate-180")}
          />
        </button>
        {menuOpen ? (
          <div className="absolute right-0 top-[calc(100%+8px)] z-50 w-48 rounded-lg border border-[#dce3ec] bg-white p-1 shadow-lg">
            <Link
              href="/student/profile"
              className="block rounded-md px-2 py-2 text-[13px] text-[#172b45] hover:bg-[#f8fafc]"
              onClick={() => setMenuOpen(false)}
            >
              My profile
            </Link>
            <Link
              href="/"
              className="block rounded-md px-2 py-2 text-[13px] text-[#172b45] hover:bg-[#f8fafc]"
              onClick={() => setMenuOpen(false)}
            >
              Module launcher
            </Link>
            <Link
              href="/login?portal=student-performance&next=%2Fstudent%2Fdashboard"
              className="block rounded-md px-2 py-2 text-[13px] text-[#172b45] hover:bg-[#f8fafc]"
              onClick={() => setMenuOpen(false)}
            >
              Switch account
            </Link>
          </div>
        ) : null}
      </div>
    </header>
  );
}