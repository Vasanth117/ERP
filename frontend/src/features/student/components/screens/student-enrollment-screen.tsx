"use client";

import {
  EnrollmentConfirmationSection,
  TermEnrollmentHistorySection,
} from "@/features/student/components/screens/student-academics-sections";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import { useAcademicDetails } from "@/features/student/hooks/use-student-academics";

/** Enrollment tab — ST 02.09 (top) then ST 02.10 (bottom). */
export function StudentEnrollmentScreen() {
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
            <EnrollmentConfirmationSection data={academics.data} />
            <TermEnrollmentHistorySection data={academics.data} />
          </>
        ) : null}
      </QueryState>
    </div>
  );
}