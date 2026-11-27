import { Suspense } from "react";

import { SyllabusScreen } from "@/features/student/components/screens/syllabus-screen";

export default function Page() {
  return (
    <Suspense fallback={null}>
      <SyllabusScreen />
    </Suspense>
  );
}