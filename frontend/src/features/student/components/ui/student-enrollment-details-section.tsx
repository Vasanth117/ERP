"use client";

import Link from "next/link";

import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import {
  ProfileDetailGrid,
  ProfilePanel,
} from "@/features/student/components/ui/student-profile-ui";
import {
  formatEnrollmentSection,
  formatEnrollmentStatusLabel,
} from "@/features/student/lib/format-enrollment-display";
import type { AcademicDetails } from "@/features/student/types/academics";

type StudentEnrollmentDetailsSectionProps = {
  data: AcademicDetails;
  /** Show heading block (ST 02.02 standalone page). Hide when embedded in overview. */
  showHeading?: boolean;
  className?: string;
};

/**
 * ST 02.02 — read-only official enrollment record (ProfilePanel layout).
 * Data source: `GET /api/v1/students/me/academics` via `useAcademicDetails`.
 */
export function StudentEnrollmentDetailsSection({
  data,
  showHeading = false,
  className,
}: StudentEnrollmentDetailsSectionProps) {
  const admission = data.admission;
  const info = data.academic_information;
  const section = formatEnrollmentSection(admission.programme_code, admission.section_code);
  const batch = info.batch_display ?? admission.batch_label ?? "—";
  const status = formatEnrollmentStatusLabel(data.enrollment_status.enrollment_status);

  return (
    <section className={className} data-figma-frame="ST-02.02" id="official-enrollment">
      {showHeading ? (
        <header className="mb-5">
          <h2 className="text-[26px] font-bold tracking-tight text-[#111827]">
            Student Enrollment Details
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">Official enrollment record</p>
        </header>
      ) : null}

      <div className="grid items-start gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <ProfilePanel title="Enrollment" figmaNode="ST-02.02-enrollment">
            <ProfileDetailGrid
              variant="personal"
              rows={[
                [
                  { label: "Register number", value: admission.roll_number ?? "—" },
                  { label: "Admission number", value: admission.admission_number ?? "—" },
                ],
                [
                  { label: "Batch", value: batch },
                  { label: "Section", value: section },
                ],
                [
                  { label: "Admission year", value: info.admission_year ?? "—" },
                  { label: "Enrollment status", value: status },
                ],
                [
                  { label: "Regulation", value: info.regulation_label ?? "—" },
                  { label: "Mode", value: info.study_mode?.trim() || "—" },
                ],
              ]}
            />
          </ProfilePanel>

          <p className="mt-3 text-[12px] text-[#8a98aa]">
            Need a programme or section change?{" "}
            <Link
              href="/student/academics/enrollment-requests"
              className="font-semibold text-[#245dd8] hover:underline"
            >
              Submit an enrollment request
            </Link>
            .
          </p>
        </div>

        <div className="lg:col-span-2">
          <EnrollmentLockedPanel />
        </div>
      </div>
    </section>
  );
}

export function EnrollmentLockedPanel() {
  return (
    <ProfilePanel title="Locked by the college" figmaNode="ST-02.02-locked">
      <div className="rounded-lg border border-[#e8ecf2] bg-[#f8fafc] p-4">
        <div className="flex items-start gap-3">
          <CollegeAdminIcon name="lock" size={18} className="mt-0.5 shrink-0 text-[#607086]" />
          <div className="min-w-0 flex-1">
            <p className="text-[13px] leading-relaxed text-[#374151]">
              Programme, batch and regulation can be changed only through the college workflow.
            </p>
            <div className="mt-3">
              <span className="inline-flex items-center gap-1 rounded-full bg-[#f3f4f6] px-2.5 py-0.5 text-[11px] font-semibold text-[#6b7280]">
                <span className="size-1.5 rounded-full bg-[#6b7280]" aria-hidden />
                Read only
              </span>
            </div>
          </div>
        </div>
      </div>
      <p className="mt-3 text-[11px] leading-relaxed text-[#8a98aa]">
        Contact your class advisor or department office if any official field is incorrect.
      </p>
    </ProfilePanel>
  );
}