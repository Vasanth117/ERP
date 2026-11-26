"use client";

import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import {
  CourseCreditSummarySection,
  SemesterSubjectListSection,
} from "@/features/student/components/screens/student-academics-sections";
import { useAcademicDetails } from "@/features/student/hooks/use-student-academics";

/** Subjects & Credits tab — ST 02.07 (top) then ST 02.06 (bottom). */
export function StudentSubjectsCreditsScreen() {
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
            <CourseCreditSummarySection data={academics.data} />
            <SemesterSubjectListSection data={academics.data} />
          </>
        ) : null}
      </QueryState>
    </div>
  );
}