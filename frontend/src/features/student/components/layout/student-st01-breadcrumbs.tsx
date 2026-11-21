"use client";

import Link from "next/link";

import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";

/** Figma ST 01.01 — breadcrumbs (node 164:219). */
export function StudentSt01Breadcrumbs({ current }: { current: string }) {
  return (
    <nav
      className="mb-2 flex flex-wrap items-center gap-2 pt-3.5 text-[13px] text-[#607086]"
      aria-label="Breadcrumb"
      data-figma-node="164:219"
    >
      <Link href="/" className="hover:text-[#245dd8]">
        Student
      </Link>
      <CollegeAdminIcon name="chevron-right" size={12} className="text-[#8a98aa]" />
      <Link href="/student/dashboard" className="hover:text-[#245dd8]">
        Dashboard
      </Link>
      <CollegeAdminIcon name="chevron-right" size={12} className="text-[#8a98aa]" />
      <span className="font-medium text-[#172b45]">{current}</span>
    </nav>
  );
}