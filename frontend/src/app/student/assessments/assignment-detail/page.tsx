import { Suspense } from "react";

import { StudentScreen } from "@/features/student/components/student-screen";

function PageInner() {
  return <StudentScreen slug="assignment-detail" />;
}

export default function Page() {
  return (
    <Suspense fallback={null}>
      <PageInner />
    </Suspense>
  );
}
