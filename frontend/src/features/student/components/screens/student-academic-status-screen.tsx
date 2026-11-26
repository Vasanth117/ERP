"use client";

import { AcademicStatusDetailsSection } from "@/features/student/components/screens/student-academics-sections";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import { useAcademicDetails } from "@/features/student/hooks/use-student-academics";

/** Status tab — ST 02.11 Academic Status Details. */
export function StudentAcademicStatusScreen() {
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
        {academics.data ? <AcademicStatusDetailsSection data={academics.data} /> : null}
      </QueryState>
    </div>
  );
}