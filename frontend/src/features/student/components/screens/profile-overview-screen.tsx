"use client";

import Link from "next/link";

import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import {
  ProfileDetailGrid,
  ProfileExploreCardGrid,
  ProfileHeaderCard,
  ProfilePageHeading,
  ProfilePanel,
  ProfileQuickLinkList,
  formatStandingLabel,
  profileInitials,
  type ProfileExploreLink,
} from "@/features/student/components/ui/student-profile-ui";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import { useEnrollmentStatus } from "@/features/student/hooks/use-student-academics";
import { useStudentDashboard } from "@/features/student/hooks/use-student-dashboard";
import { useStudentProfile } from "@/features/student/hooks/use-student-profile";
import { STUDENT_BTN_PRIMARY } from "@/features/student/components/ui/student-portal-tokens";
import { formatStudentSemesterNumber } from "@/features/student/lib/format-semester";

const EXPLORE_CARDS: ProfileExploreLink[] = [
  {
    title: "Personal information",
    description: "Identity, admission and official IDs",
    href: "/student/profile/personal",
    icon: "user-round",
    figmaNode: "164:720",
    tone: "blue",
  },
  {
    title: "Academic profile",
    description: "Programme, enrollments and standing",
    href: "/student/profile/academic",
    icon: "book-open",
    figmaNode: "164:1025",
    tone: "purple",
  },
  {
    title: "Contact information",
    description: "Phone, email and addresses",
    href: "/student/profile/contact",
    icon: "phone",
    figmaNode: "164:1327",
    tone: "green",
  },
  {
    title: "Guardian information",
    description: "Emergency contacts and guardians",
    href: "/student/profile/guardian",
    icon: "users",
    figmaNode: "164:1634",
    tone: "amber",
  },
];

export function StudentProfileOverviewScreen() {
  const profile = useStudentProfile();
  const enrollment = useEnrollmentStatus();
  const dashboard = useStudentDashboard();

  const semesterDisplay = formatStudentSemesterNumber(
    dashboard.data?.academic_term ??
      (enrollment.data
        ? {
            semester_number: null,
            semester_label: enrollment.data.semester_label,
          }
        : null),
  );

  const sectionLabel = profile.data?.section_code ? `Section ${profile.data.section_code}` : null;

  const metaLine = profile.data
    ? [
        profile.data.roll_number,
        profile.data.programme_name ?? profile.data.programme_code,
        semesterDisplay !== "—" ? semesterDisplay : null,
        sectionLabel,
      ]
        .filter(Boolean)
        .join(" · ")
    : "";

  const batchYear =
    profile.data?.batch_label ??
    (profile.data?.admission_date
      ? String(new Date(profile.data.admission_date).getFullYear())
      : "—");

  return (
    <div className="space-y-5" data-figma-node="164:391">
      <ProfilePageHeading
        title="Student Profile Overview"
        description="Official student record for the active term"
        actions={
          <Link href="/student/profile/edit" className={STUDENT_BTN_PRIMARY}>
            <CollegeAdminIcon name="pencil" size={15} className="text-white" />
            Edit permitted fields
          </Link>
        }
      />

      <QueryState
        query={profile}
        isLoading={profile.isLoading}
        isError={profile.isError}
        error={profile.error}
        onRetry={() => void profile.refetch()}
      >
        {profile.data ? (
          <>
            <ProfileHeaderCard
              initials={profileInitials(profile.data.full_name)}
              fullName={profile.data.full_name}
              badges={[
                {
                  label: formatStandingLabel(enrollment.data?.enrollment_status ?? "Active"),
                  tone: "success",
                },
                {
                  label: formatStandingLabel(enrollment.data?.progression_status ?? "Regular"),
                  tone: "info",
                },
              ]}
              metaLine={metaLine}
              email={profile.data.email}
              phone={profile.data.contact_phone ?? "—"}
              batchLabel={batchYear}
            />

            <div className="grid gap-5 xl:grid-cols-3">
              <div className="xl:col-span-2">
                <ProfilePanel title="Student overview">
                  <ProfileDetailGrid
                    rows={[
                      [
                        { label: "Register number", value: profile.data.roll_number ?? "—" },
                        { label: "Programme", value: profile.data.programme_name ?? "—" },
                      ],
                      [
                        { label: "Department", value: profile.data.department_name ?? "—" },
                        { label: "Semester", value: semesterDisplay },
                      ],
                      [
                        { label: "Section", value: profile.data.section_code ?? "—" },
                        {
                          label: "Admission year",
                          value: batchYear,
                        },
                      ],
                    ]}
                  />
                </ProfilePanel>
              </div>

              <div className="xl:col-span-1">
                <ProfilePanel title="Quick links">
                  <ProfileQuickLinkList
                    links={[
                      {
                        title: "Personal information",
                        href: "/student/profile/personal",
                        icon: "user-round",
                      },
                      {
                        title: "Academic profile",
                        href: "/student/profile/academic",
                        icon: "book-open",
                      },
                      {
                        title: "Request update",
                        href: "/student/profile/update-requests",
                        icon: "pencil",
                      },
                      {
                        title: "Documents",
                        description: `${profile.data.document_refs.length} on record`,
                        href: "/student/documents",
                        icon: "file-text",
                      },
                    ]}
                  />
                </ProfilePanel>
              </div>
            </div>

            <section className="space-y-3">
              <h3 className="text-[14px] font-semibold text-[#172b45]">Explore profile sections</h3>
              <p className="text-[12px] text-[#607086]">
                Open each workspace for the full detail panel from your live profile.
              </p>
              <ProfileExploreCardGrid cards={EXPLORE_CARDS} />
            </section>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}