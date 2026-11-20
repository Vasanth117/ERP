"use client";

import Link from "next/link";

import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import { EntryArrow } from "@/features/landing/components/entry-arrow";
import { studentNavGroups, type StudentNavItem } from "@/features/student/config/navigation";
import { PageHeading } from "@/features/student/components/ui/student-screen-ui";

const FIGMA_SECTIONS: { figmaPage: string; title: string; description: string }[] = [
  {
    figmaPage: "ST 01",
    title: "Dashboard & Profile",
    description: "Dashboard, profile, and account activity.",
  },
  {
    figmaPage: "ST 02",
    title: "Academic Management & Enrollment",
    description: "Enrollment status, history, eligibility, and requests.",
  },
  {
    figmaPage: "ST 03",
    title: "Course, Subject & Curriculum",
    description: "Programme curriculum, courses, syllabus, and outcomes.",
  },
  {
    figmaPage: "ST 04",
    title: "Course Registration & Electives",
    description: "Registration window, electives, and course selection.",
  },
  {
    figmaPage: "ST 05",
    title: "Timetable & Calendar",
    description: "Daily and weekly views, academic calendar, exams, and changes.",
  },
  {
    figmaPage: "ST 06",
    title: "Attendance",
    description: "Summary, history, shortages, eligibility, export, and discrepancies.",
  },
  {
    figmaPage: "ST 07",
    title: "CIA Marks",
    description: "Schedules, published marks, corrections, and component detail.",
  },
  {
    figmaPage: "ST 08",
    title: "Continuous Assessment",
    description: "Assignments, quizzes, submissions, feedback, and resubmission.",
  },
];

function itemsForFigmaPage(figmaPage: string): StudentNavItem[] {
  const out: StudentNavItem[] = [];
  for (const group of studentNavGroups) {
    for (const item of group.items) {
      if (item.figmaPage === figmaPage) out.push(item);
    }
  }
  return out;
}

export function StudentPortalHomeScreen() {
  return (
    <div>
      <PageHeading
        title="Student Portal"
        description="All student workspace pages (ST 00–08). Each screen loads live data from the student API."
        figmaPage="ST 00"
      />

      <div className="space-y-10">
        {FIGMA_SECTIONS.map((section) => {
          const items = itemsForFigmaPage(section.figmaPage);
          return (
            <section key={section.figmaPage} aria-labelledby={`section-${section.figmaPage}`}>
              <SectionHeader section={section} />
              <ul className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {items.map((item) => (
                  <li key={item.id}>
                    <PortalPageCard item={item} />
                  </li>
                ))}
              </ul>
            </section>
          );
        })}
      </div>
    </div>
  );
}

function PortalPageCard({ item }: { item: StudentNavItem }) {
  return (
    <Link
      href={item.href}
      className="group flex h-full min-h-[88px] items-center gap-3 rounded-2xl border border-[#e3e9f2] bg-white px-3.5 py-4 shadow-[0px_1px_1px_rgba(23,43,69,0.04),0px_4px_7px_rgba(23,43,69,0.05)] transition-[border-color,box-shadow] hover:border-[#245dd8] hover:shadow-[0px_2px_6px_rgba(23,43,69,0.06),0px_12px_28px_rgba(36,93,216,0.18)]"
    >
      <div className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-[#eff6ff]">
        <CollegeAdminIcon name={item.icon} size={22} className="text-[#245dd8]" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="min-w-0 flex-1 text-sm font-semibold leading-snug text-[#172b45] group-hover:text-[#245dd8]">
            {item.label}
          </p>
          <EntryArrow tone="default" />
        </div>
        <p className="mt-1 truncate text-[11px] text-[#9ca3af]">{item.href}</p>
      </div>
    </Link>
  );
}

function SectionHeader({
  section,
}: {
  section: (typeof FIGMA_SECTIONS)[number];
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-2 border-b border-[#e8ecf2] pb-3">
      <div>
        <p id={`section-${section.figmaPage}`} className="text-xs font-semibold uppercase tracking-wide text-[#245dd8]">
          {section.figmaPage}
        </p>
        <h2 className="mt-1 text-lg font-semibold text-[#111827]">{section.title}</h2>
        <p className="mt-0.5 text-sm text-[#607086]">{section.description}</p>
      </div>
      <span className="rounded-full bg-[#f3f4f6] px-2.5 py-0.5 text-[11px] font-medium text-[#6b7280]">
        {itemsForFigmaPage(section.figmaPage).length} pages
      </span>
    </div>
  );
}
