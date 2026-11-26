"use client";

import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import {
  AcademicProgressionDetailsSection,
  CurrentSemesterOverviewSection,
  SemesterAcademicHistorySection,
} from "@/features/student/components/screens/student-academics-sections";
import { useAcademicDetails } from "@/features/student/hooks/use-student-academics";

/** Semesters tab — ST 02.04 → 02.05 → 02.08 (single scroll). */
export function StudentSemestersScreen() {
  const academics = useAcademicDetails();

  return (
    <div className="space-y-10" data-figma-page="ST 02">
      <QueryState
        query={academics}
        isLoading={academics.isLoading}
        isError={academics.isError}
        error={academics.error}
        onRetry={() => void academics.refetch()}
      >
        {academics.data ? (
          <>
            <CurrentSemesterOverviewSection data={academics.data} />
            <SemesterAcademicHistorySection data={academics.data} />
            <AcademicProgressionDetailsSection data={academics.data} />
          </>
        ) : null}
      </QueryState>
    </div>
  );
}