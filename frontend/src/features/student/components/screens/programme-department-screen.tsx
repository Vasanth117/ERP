"use client";

import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import { ProgrammeDepartmentDetailsSection } from "@/features/student/components/screens/student-academics-sections";
import { useAcademicDetails } from "@/features/student/hooks/use-student-academics";

/** Programme & Department tab — ST 02.03 only (Figma 164:4368). */
export function ProgrammeDepartmentScreen() {
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
        {academics.data ? <ProgrammeDepartmentDetailsSection data={academics.data} /> : null}
      </QueryState>
    </div>
  );
}