"use client";

import {
  ProfileAcademicOverviewButton,
  ProfileAdvisorPanel,
  ProfileDetailGrid,
  ProfilePageHeading,
  ProfilePanel,
} from "@/features/student/components/ui/student-profile-ui";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import { useAcademicDetails } from "@/features/student/hooks/use-student-academics";
import { useStudentProfile } from "@/features/student/hooks/use-student-profile";
import { formatStudentSemesterNumber } from "@/features/student/lib/format-semester";

function departmentShortLabel(
  programmeCode: string | null | undefined,
  departmentName: string | null | undefined,
): string {
  if (departmentName?.trim()) {
    return departmentName.trim();
  }
  if (!programmeCode) return "—";
  const parts = programmeCode.split("-");
  return parts[parts.length - 1] ?? programmeCode;
}

/** ST 01.04 — Academic Profile (Figma node 164:1025). */
export function StudentProfileAcademicScreen() {
  const academics = useAcademicDetails();
  const profile = useStudentProfile();

  const isLoading = academics.isLoading || profile.isLoading;
  const isError = academics.isError && !profile.data;

  return (
    <div className="space-y-5" data-figma-node="164:1025">
      <ProfilePageHeading
        title="Academic Profile"
        description="Programme, batch and regulation"
        backHref="/student/profile"
        actions={<ProfileAcademicOverviewButton />}
      />
      <QueryState
        query={academics}
        isLoading={isLoading}
        isError={isError}
        error={academics.error}
        onRetry={() => void academics.refetch()}
      >
        {profile.data ? (
          <AcademicProfileBody
            academics={academics.data}
            profile={profile.data}
          />
        ) : null}
      </QueryState>
    </div>
  );
}

function AcademicProfileBody({
  academics,
  profile,
}: {
  academics: ReturnType<typeof useAcademicDetails>["data"];
  profile: NonNullable<ReturnType<typeof useStudentProfile>["data"]>;
}) {
  const info = academics?.academic_information;
  const advisors = academics?.advisors;
  const deptProgramme = academics?.department_programme;
  const admission = academics?.admission;

  const programme =
    deptProgramme?.programme_name ?? profile.programme_name ?? admission?.programme_name ?? "—";
  const department = departmentShortLabel(
    deptProgramme?.programme_code ?? profile.programme_code,
    deptProgramme?.department_name ?? profile.department_name ?? admission?.department_name,
  );
  const regulation = info?.regulation_label ?? "—";
  const batch = info?.batch_display ?? profile.batch_label ?? admission?.batch_label ?? "—";
  const admissionType = info?.admission_type ?? "—";
  const rollNumber = profile.roll_number ?? admission?.roll_number ?? "—";
  const semester =
    info?.current_semester_number != null
      ? String(info.current_semester_number)
      : formatStudentSemesterNumber(null);

  return (
    <div className="grid items-start gap-6 lg:grid-cols-5">
      <div className="lg:col-span-3">
        <ProfilePanel title="Academic information" figmaNode="164:1271">
          <ProfileDetailGrid
            variant="personal"
            rows={[
              [
                { label: "Programme", value: programme },
                { label: "Department", value: department },
              ],
              [
                { label: "Regulation", value: regulation },
                { label: "Batch", value: batch },
              ],
              [
                { label: "Admission type", value: admissionType },
                { label: "Roll number", value: rollNumber },
              ],
              [
                { label: "Current semester", value: semester },
                { label: "Section", value: profile.section_code ?? admission?.section_code ?? "—" },
              ],
            ]}
          />
        </ProfilePanel>
      </div>
      <div className="lg:col-span-2">
        <ProfileAdvisorPanel
          classAdvisorName={advisors?.class_advisor_name}
          mentorName={advisors?.mentor_name}
        />
      </div>
    </div>
  );
}